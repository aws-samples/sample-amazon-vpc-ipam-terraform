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

variable "provider_region" {
  description = "AWS region where IPAM will be deployed and managed."
  type        = string

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]{1}$", var.provider_region))
    error_message = "Provider region must be a valid AWS region name (e.g., us-east-1, eu-west-1)."
  }
}

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

  validation {
    condition     = alltrue([for region in var.operating_regions : can(regex("^[a-z]{2}-[a-z]+-[0-9]{1}$", region))])
    error_message = "All operating regions must be valid AWS region names (e.g., us-east-1, eu-west-1)."
  }
}

variable "share_name" {
  description = <<-EOT
    Name of the RAM share for IPAM resources.
    This name will be used to identify shared resources across accounts.
    Should be descriptive of the shared IPAM resource purpose.
  EOT
  type        = string

  validation {
    condition     = length(var.share_name) >= 3 && length(var.share_name) <= 128
    error_message = "Share name must be between 3 and 128 characters."
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

  validation {
    condition     = length(var.top_name) >= 3 && length(var.top_name) <= 128
    error_message = "Top pool name must be between 3 and 128 characters."
  }
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

  validation {
    condition     = alltrue([for cidr in var.top_cidr : can(regex("^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\\/([0-9]|[1-2][0-9]|3[0-2]))$", cidr))])
    error_message = "Top-level CIDR must be a valid IPv4 CIDR block (e.g., 10.0.0.0/8)."
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
  type        = map(object({
    name        = string  # Display name for the regional pool
    description = string  # Detailed description of the regional pool's purpose
    cidr        = list(string)  # List containing single CIDR allocation for this region
    locale      = string  # AWS region identifier (e.g., us-east-1)
  }))

  validation {
    condition     = length(var.reg_ipam_configs) > 0
    error_message = "At least one regional IPAM configuration must be specified."
  }

  validation {
    condition = alltrue([
      for k, v in var.reg_ipam_configs :
        can(regex("^[a-z]{2}-[a-z]+-[0-9]{1}$", v.locale))
    ])
    error_message = "Each regional IPAM configuration must have a valid AWS region locale."
  }

  validation {
    condition = alltrue([
      for k, v in var.reg_ipam_configs :
        length(v.cidr) == 1 &&
        can(regex("^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\\/([0-9]|[1-2][0-9]|3[0-2]))$", v.cidr[0]))
    ])
    error_message = "Each regional IPAM configuration must have exactly one valid IPv4 CIDR block."
  }
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
  type        = map(map(object({
    name        = string  # Display name for the business unit pool
    description = string  # Detailed description of the business unit pool's purpose
    cidr        = list(string)  # List containing single CIDR allocation for this business unit
  })))

  validation {
    condition     = length(var.bu_ipam_configs) > 0
    error_message = "At least one business unit IPAM configuration must be specified."
  }

  validation {
    condition = alltrue(flatten([
      for region, bus in var.bu_ipam_configs : [
        for bu, config in bus :
          length(config.cidr) == 1 &&
          can(regex("^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\\/([0-9]|[1-2][0-9]|3[0-2]))$", config.cidr[0]))
      ]
    ]))
    error_message = "Each business unit IPAM configuration must have exactly one valid IPv4 CIDR block."
  }
}

variable "env_ipam_configs" {
  description = <<-EOT
    Configuration for environment-specific IPAM pools within each business unit and region.
    Defines IP allocations for each environment within each business unit and region.
    Each environment should receive a non-overlapping portion of its parent business unit CIDR.
    
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
  type        = map(map(map(object({
    name          = string  # Display name for the environment pool
    description   = string  # Detailed description of the environment pool
    cidr          = list(string)  # List containing single CIDR for this environment
    reserved_cidr = string  # Optional CIDR to reserve within this environment
  }))))

  validation {
    condition     = length(var.env_ipam_configs) > 0
    error_message = "At least one environment IPAM configuration must be specified."
  }

  validation {
    condition = alltrue(flatten([
      for region, bus in var.env_ipam_configs : [
        for bu, envs in bus : [
          for env, env_config in envs :
            length(env_config.cidr) == 1 &&
            can(regex("^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\\/([0-9]|[1-2][0-9]|3[0-2]))$", env_config.cidr[0])) &&
            (env_config.reserved_cidr == "" || can(regex("^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\\/([0-9]|[1-2][0-9]|3[0-2]))$", env_config.reserved_cidr)))
        ]
      ]
    ]))
    error_message = "Each environment IPAM configuration must have exactly one valid IPv4 CIDR block and an optional valid reserved CIDR."
  }
}
