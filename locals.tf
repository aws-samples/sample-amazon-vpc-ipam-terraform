#==============================================================================
# Sample Terraform Implementation for Hierarchical IPAM on AWS
#
# This code demonstrates how to implement hierarchical IP Address Management
# across multiple AWS regions, business units, and environments.
#
# IMPORTANT: This code is provided as a sample for educational purposes.
# Before using in production, review security configurations and customize
# to meet your organizational requirements.
#==============================================================================

locals {
  # Example Required Tags
  product_name  = "enterprise-ipam"
  feature_name  = "ip-address-management"
  business_unit = "infrastructure"
  environment   = "core"
  # Example Optional Tags
  optional_tags = {
    "project"    = "network-modernization"
    "stack_role" = "ipam"
    "is_live"    = "true"
  }
}
