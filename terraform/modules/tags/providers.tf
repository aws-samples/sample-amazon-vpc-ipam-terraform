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

terraform {
  # Require Terraform v1.9.1 or higher for features like:
  # - optional object attributes
  # - improved validation capabilities
  # - precondition and postcondition checks
  required_version = ">= 1.9.1, < 2.5.0"
  # Enable experimental feature for optional object attributes
  # experiments      = [module_variable_optional_attrs]
  required_providers {
    aws = {
      source = "hashicorp/aws"
      # Require AWS provider v5.11.0 or higher for:
      # - Support for advanced IPAM features
      # - Proper RAM sharing functionality
      # - Improved CIDR validation and handling
      # Upper bound to prevent unexpected breaking changes
      version = ">= 5.11.0, < 6.11.0"
      # configuration_aliases = [aws.some_alias]
    }
  }
}
