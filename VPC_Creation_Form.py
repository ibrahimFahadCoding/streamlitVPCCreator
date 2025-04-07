import streamlit as st
import boto3
import json
import os
from PIL import Image

# Set the page config and load the logo
st.set_page_config(page_title="VPC Creator", layout="centered")
logo = Image.open("assets/AlkiraLogo.png")
st.image(logo, width=180)

st.title("🔐 Secure VPC Creator")

# Config: Location for JSON file storing users
USER_FILE = "users.json"

# Check if users file exists and load it, otherwise initialize empty
if os.path.exists(USER_FILE):
    with open(USER_FILE, "r") as file:
        users = json.load(file)
else:
    users = {}

# Function to check if the user credentials are valid
def check_credentials(username, password):
    if username in users and users[username] == password:
        return True
    return False

# Authentication form
with st.form("auth_form"):
    st.subheader("🔑 Authenticate")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Login")

# Handle the login logic
if submitted:
    if check_credentials(username, password):
        st.success("✅ Authenticated!")
        st.session_state["authenticated"] = True
    else:
        st.error("❌ Invalid username or password.")

# Show the VPC creation form if the user is authenticated
if st.session_state.get("authenticated"):
    st.write("---")
    st.subheader("🌐 Create a New VPC")

    with st.form("vpc_form"):
        vpc_name = st.text_input("VPC Name")
        vpc_cidr = st.text_input("VPC CIDR Block", value="")
        subnet_cidrs = st.text_area("Subnet CIDR Blocks (comma-separated)", value="")
        azs = st.text_input("Availability Zones (comma-separated)", value="")
        create = st.form_submit_button("🚀 Create VPC")

    if create:
        if not vpc_name or not vpc_cidr or not subnet_cidrs or not azs:
            st.warning("Please fill out all fields.")
        else:
            try:
                # Initialize the boto3 client for EC2
                ec2 = boto3.client("ec2")

                # Create VPC
                st.write(f"Creating VPC {vpc_name} with CIDR {vpc_cidr}...")
                vpc = ec2.create_vpc(CidrBlock=vpc_cidr)
                vpc_id = vpc["Vpc"]["VpcId"]
                ec2.create_tags(Resources=[vpc_id], Tags=[{"Key": "Name", "Value": vpc_name}])

                # Enable DNS Support and DNS Hostnames for the VPC
                ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={"Value": True})
                ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={"Value": True})

                # Create Internet Gateway
                st.write(f"Creating and attaching Internet Gateway to VPC {vpc_name}...")
                igw = ec2.create_internet_gateway()
                igw_id = igw["InternetGateway"]["InternetGatewayId"]
                ec2.attach_internet_gateway(VpcId=vpc_id, InternetGatewayId=igw_id)

                # Create Subnets
                subnet_list = [s.strip() for s in subnet_cidrs.split(",")]
                az_list = [a.strip() for a in azs.split(",")]
                for i, cidr in enumerate(subnet_list):
                    st.write(f"Creating Subnet with CIDR {cidr} in Availability Zone {az_list[i % len(az_list)]}...")
                    ec2.create_subnet(VpcId=vpc_id, CidrBlock=cidr, AvailabilityZone=az_list[i % len(az_list)])

                st.success(f"✅ VPC {vpc_name} ({vpc_id}) created successfully!")

            except boto3.exceptions.Boto3Error as e:
                st.error(f"❌ AWS API Error: {e}")
                st.write("Please check your AWS credentials and permissions.")
            except Exception as e:
                st.error(f"❌ Error during VPC creation: {e}")
                st.write("An error occurred while creating the VPC. Please try again.")
