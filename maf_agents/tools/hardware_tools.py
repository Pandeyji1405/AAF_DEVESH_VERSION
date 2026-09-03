from typing import Dict, Any
from agent_framework import tool

def create_hardware_tools(ae_client):
    """
    Creates Microsoft Agent Framework (@tool) tools for CMDB & Hardware Asset Lifecycle Operations.
    """

    @tool(
        name="get_asset_details",
        description="Retrieves asset tag, serial number, model, and install status from ServiceNow CMDB."
    )
    def get_asset_details(asset_tag_or_serial: str) -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_HW_001_GetAssetDetails", {
            "asset_tag_or_serial": asset_tag_or_serial
        })
        return res.get("workflowResponse", {})

    @tool(
        name="check_warranty",
        description="Checks OEM manufacturer warranty entitlement and SLA tier for a hardware serial number."
    )
    def check_warranty(serial_number: str) -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_HW_002_CheckWarranty", {
            "serial_number": serial_number
        })
        return res.get("workflowResponse", {})

    @tool(
        name="order_replacement",
        description="Places an express dispatch order for replacement laptop/hardware via FedEx Express delivery."
    )
    def order_replacement(ci_id: str, serial_number: str, ticket_id: str, shipping_address: str = "") -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_HW_020_OrderReplacement", {
            "ci_id": ci_id,
            "serial_number": serial_number,
            "ticket_id": ticket_id,
            "shipping_address": shipping_address or "Enterprise Office - IT Hub / Employee Remote Desk"
        })
        return res.get("workflowResponse", {})

    @tool(
        name="update_ci_state",
        description="Updates the lifecycle state (e.g. Pending Replacement, In Repair) of an asset in CMDB."
    )
    def update_ci_state(ci_id: str, new_install_status: str, ticket_id: str, condition_notes: str = "") -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_HW_010_UpdateCIState", {
            "ci_id": ci_id,
            "new_install_status": new_install_status,
            "ticket_id": ticket_id,
            "condition_notes": condition_notes
        })
        return res.get("workflowResponse", {})

    return [
        get_asset_details,
        check_warranty,
        order_replacement,
        update_ci_state
    ]
