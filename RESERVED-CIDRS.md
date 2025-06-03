# Reserved CIDRs in AWS IPAM Implementation

## Overview

This document explains the "reserved CIDR" functionality implemented in the AWS VPC IPAM Terraform solution. Reserved CIDRs allow you to explicitly allocate and reserve specific CIDR blocks within environment-level IPAM pools, preventing them from being automatically assigned to other resources.

## Purpose

Reserved CIDRs serve several important purposes:

1. **Infrastructure Reservation**: Reserve address space for shared infrastructure components
2. **Future Expansion**: Set aside blocks for anticipated future needs
3. **Transition Support**: Reserve blocks that might be migrated from legacy environments
4. **Special Use Cases**: Allocate blocks for specific networking requirements (e.g., VPC Transit Gateway attachments)
5. **Compliance Requirements**: Fulfill regulatory or organizational policies that require specific address allocations

## How to Use

### Specifying Reserved CIDRs

Reserved CIDRs are defined in the `env_ipam_configs` variable structure, which defines environment-specific IPAM pools. Each environment can have an optional `reserved_cidr` parameter:

```hcl
env_ipam_configs = {
  us-east-1 = {
    finance = {
      dev = {
        name          = "Finance Dev"
        description   = "Finance Development Environment"
        cidr          = ["10.0.0.0/16"]
        reserved_cidr = "10.0.0.0/24"  # This block will be explicitly reserved
      }
    }
  }
}
```

To specify a reserved CIDR:

1. Ensure it is a valid CIDR notation (e.g., "10.0.0.0/24")
2. The CIDR must be a subset of the environment's CIDR block
3. Leave it as an empty string (`""`) if no reservation is needed

### Validation

The implementation includes validation to ensure:

1. Reserved CIDRs are valid CIDR blocks
2. Reserved CIDRs are proper subnets of their parent environment CIDR
3. There are no conflicts with other allocations

If validation fails, Terraform will display an error message explaining the issue.

## Implementation Details

The reserved CIDR functionality is implemented through the following components:

### 1. Local Variables (terraform/modules/ipam/locals.tf)

- `env_reserved_cidrs`: Extracts all environment configurations with non-empty reserved CIDRs
- `reserved_cidr_allocations`: Converts to a map with unique keys for resource creation
- `reserved_cidr_validation`: Validates that each reserved CIDR is within its parent environment CIDR

### 2. CIDR Allocations (terraform/modules/ipam/main.tf)

- `aws_vpc_ipam_pool_cidr_allocation.reserved_cidr`: Creates explicit allocations for each reserved CIDR
- Includes lifecycle precondition to validate proper containment
- Sets a descriptive name for each allocation for easier identification

## Best Practices

1. **Size Appropriately**: Reserve only the CIDR space you actually need
2. **Document Purpose**: Use descriptive names and include the purpose in your configuration
3. **Validate Containment**: Ensure reserved CIDRs are proper subnets of their parent environment CIDRs
4. **Avoid Fragmentation**: Place reserved CIDRs at the beginning or end of environment ranges to avoid fragmentation
5. **Consider Future Growth**: Account for growth when sizing both environment pools and their reserved portions

## Limitations

1. Reserved CIDRs are static and defined during deployment
2. Each environment can have only one reserved CIDR block (though this can be a larger block subdivided later)
3. Reserved CIDR blocks cannot overlap with existing allocations
4. Changes to reserved CIDRs may require careful coordination if resources already use addresses in that range
5. No automated way to convert existing allocations to reserved blocks (would require manual steps)

## Example

```hcl
# terraform/terraform.tfvars
env_ipam_configs = {
  us-east-1 = {
    marketing = {
      dev = {
        name          = "Marketing Dev"
        description   = "Marketing Development Environment"
        cidr          = ["10.100.0.0/16"]
        reserved_cidr = "10.100.0.0/24"  # First /24 reserved for shared services
      },
      test = {
        name          = "Marketing Test"
        description   = "Marketing Test Environment"
        cidr          = ["10.101.0.0/16"]
        reserved_cidr = "10.101.255.0/24"  # Last /24 reserved for future expansion
      }
    }
  }
}
```

In this example:
- The Marketing Dev environment reserves the first /24 subnet (10.100.0.0/24) for shared services
- The Marketing Test environment reserves the last /24 subnet (10.101.255.0/24) for future expansion
