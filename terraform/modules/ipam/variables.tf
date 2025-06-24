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

#=============================================
# Core Configuration Variables
#=============================================

variable "operating_regions" {
  description = <<-EOT
    Regions where IPAM operates and manages resources.
    Must be valid AWS region names like us-east-1, eu-west-1, etc.
    At least one region must be specified.
  EOT
  type        = list(string)

  validation {
    condition     = length(var.operating_regions) > 0
    error_message = "At least one operating region must be specified."
  }
}

variable "share_name" {
  description = <<-EOT
    Name of the RAM share for IPAM resources.
    This name will be used to identify shared resources across accounts.
    Should be descriptive of the shared IPAM resource purpose.
  EOT
  type        = string
}

variable "organization_arn" {
  description = <<-EOT
    The ARN of the AWS Organization or specific account to share IPAM resources with.
    Typically this is the ARN of your entire AWS Organization.
    Format: arn:aws:organizations::<management-account-id>:organization/o-<organization-id>
  EOT
  type        = string

  validation {
    condition     = can(regex("^arn:aws:organizations::", var.organization_arn))
    error_message = "Organization ARN must be a valid AWS Organizations ARN."
  }
}

#=============================================
# IPAM Pool Configuration Variables
#=============================================

variable "top_name" {
  description = <<-EOT
    Name of the top-level IPAM pool.
    This is the root pool that contains all regional allocations.
    Should be descriptive of your organization's entire IP space.
  EOT
  type        = string
}

variable "top_description" {
  description = <<-EOT
    Description of the top-level IPAM pool.
    Should provide context about the organizational IP space allocation strategy.
    This appears in the AWS console and helps administrators understand the pool's purpose.
  EOT
  type        = string
}

variable "top_cidr" {
  description = <<-EOT
    CIDR block for the top-level IPAM pool.
    This represents your organization's entire IP address space.
    Example: ["10.0.0.0/8"] for a standard RFC1918 private address space.
    Only one CIDR block is currently supported at this level.
  EOT
  type        = list(string)

  validation {
    condition     = length(var.top_cidr) == 1
    error_message = "Exactly one top-level CIDR block must be specified."
  }
}

variable "reg_ipam_configs" {
  description = <<-EOT
    Configuration for regional IPAM pools.
    Defines IP allocations for each AWS region where IPAM will operate.
    Each region should receive a non-overlapping portion of the top-level CIDR.
    
    Example:
    {
      us_east_1 = {
        name        = "US East 1 Region"
        description = "US East 1 Regional Pool"
        cidr        = ["10.0.0.0/12"]
        locale      = "us-east-1"
      }
    }
  EOT
  type = map(object({
    name        = string       # Display name for the regional pool
    description = string       # Detailed description of the regional pool's purpose
    cidr        = list(string) # List containing single CIDR allocation for this region
    locale      = string       # AWS region identifier (e.g., us-east-1)
  }))
}

variable "bu_ipam_configs" {
  description = <<-EOT
    Configuration for Business Unit IPAM pools.
    Defines IP allocations for each business unit within each region.
    Organized as a map of regions to business units to configurations.
    Each business unit should receive a non-overlapping portion of its regional CIDR.
    
    Example:
    {
      us_east_1 = {
        finance = {
          name        = "Finance BU"
          description = "Finance Business Unit Pool"
          cidr        = ["10.0.0.0/14"]
        }
      }
    }
  EOT
  type = map(map(object({
    name        = string       # Display name for the business unit pool
    description = string       # Detailed description of the business unit pool's purpose
    cidr        = list(string) # List containing single CIDR allocation for this business unit
  })))
}

variable "env_ipam_configs" {
  description = <<-EOT
    Configuration for environment-specific IPAM pools.
    Defines IP allocations for each environment within each business unit and region.
    Each environment should receive a non-overlapping portion of its parent business unit CIDR.
    The variable structure allows for flexible environment names to support various organizational structures.
    
    Example:
    {
      us_east_1 = {
        finance = {
          core = {
            name          = "Finance Core"
            description   = "Finance Core Infrastructure"
            cidr          = ["10.0.0.0/16"]
            reserved_cidr = "10.0.0.0/24"  # Optional reserved block
          }
        }
      }
    }
    
    Note: The reserved_cidr is an optional subnet that can be explicitly reserved within
    the environment CIDR block for specific purposes (e.g., shared services, gateways).
  EOT
  type = map(map(map(object({
    name          = string       # Display name for the environment pool
    description   = string       # Detailed description of the environment pool
    cidr          = list(string) # List containing single CIDR for this environment
    reserved_cidr = string       # Optional CIDR to reserve within this environment
  }))))
}

#=============================================
# Resource Tagging
#=============================================

variable "tags" {
  description = <<-EOT
    Map of tags to apply to all resources created in the IPAM module.
    These tags will be applied to IPAM pools, RAM shares, and other resources.
    Used for resource governance, cost allocation, and operational visibility.
  EOT
  type        = map(string)
  default     = {}
}
