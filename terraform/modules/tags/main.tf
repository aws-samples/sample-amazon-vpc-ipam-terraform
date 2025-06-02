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
  tag_map = merge(
    {
      product_name  = var.product_name
      feature_name  = var.feature_name
      business_unit = var.business_unit
      environment   = var.environment
    },
    var.optional_tags
  )
}
