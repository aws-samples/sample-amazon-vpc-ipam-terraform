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

module "tags" {
  source = "./modules/tags"
  # Pass Example Required Tags to Tagging Submodule
  product_name  = local.product_name
  feature_name  = local.feature_name
  business_unit = local.business_unit
  environment   = local.environment
  # Pass Example Optional Tags to Tagging Submodule
  optional_tags = local.optional_tags
}
