import streamlit as st
import boto3
from PIL import Image

st.set_page_config(page_title="Delete VPCs", layout="wide")
logo = Image.open("assets/AlkiraLogo.png")
st.image(logo, width=180)

st.title("🗑️ Delete VPCs")

# Connect to EC2
ec2 = boto3.client("ec2")

# Get list of VPCs
response = ec2.describe_vpcs()
vpcs = [
    {
        "VpcId": v["VpcId"],
        "Name": next((t["Value"] for t in v.get("Tags", []) if t["Key"] == "Name"), "No Name"),
        "IsDefault": v.get("IsDefault", False)
    }
    for v in response["Vpcs"]
    if not v.get("IsDefault", False)  # skip default VPCs
]

if not vpcs:
    st.info("No non-default VPCs found.")
else:
    st.write("### Existing VPCs")
    for i, vpc in enumerate(vpcs):
        col1, col2, col3 = st.columns([3, 4, 2])
        col1.write(f"**{vpc['VpcId']}**")
        col2.write(vpc['Name'])
        delete_clicked = col3.button("🗑️ Delete", key=f"delete_{i}")

        if delete_clicked:
            with st.spinner(f"Deleting VPC {vpc['VpcId']}..."):
                try:
                    vpc_id = vpc["VpcId"]

                    # Detach & delete Internet Gateways
                    igws = ec2.describe_internet_gateways(
                        Filters=[{"Name": "attachment.vpc-id", "Values": [vpc_id]}]
                    )["InternetGateways"]
                    for igw in igws:
                        igw_id = igw["InternetGatewayId"]
                        ec2.detach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
                        ec2.delete_internet_gateway(InternetGatewayId=igw_id)

                    # Delete Subnets
                    subnets = ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vpc_id]}])["Subnets"]
                    for subnet in subnets:
                        ec2.delete_subnet(SubnetId=subnet["SubnetId"])

                    # Delete Route Tables (excluding the main one)
                    rtbs = ec2.describe_route_tables(Filters=[{"Name": "vpc-id", "Values": [vpc_id]}])["RouteTables"]
                    for rtb in rtbs:
                        if not any(a.get("Main") for a in rtb.get("Associations", [])):
                            ec2.delete_route_table(RouteTableId=rtb["RouteTableId"])

                    # Finally delete the VPC
                    ec2.delete_vpc(VpcId=vpc_id)
                    st.success(f"✅ VPC {vpc_id} deleted successfully.")

                except Exception as e:
                    st.error(f"❌ Failed to delete VPC {vpc_id}: {e}")
            st.rerun()

