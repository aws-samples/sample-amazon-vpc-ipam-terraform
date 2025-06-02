# Terraform Tagging Module

This submodule contains a sample Terraform implementation demonstrating how to ensure consistent tagging across AWS resources defined in Terraform configurations. This sample is intended for educational purposes and shows one possible approach to centralizing and simplifying the process of standardizing and applying tags.

---

## Input Variables

| Name          | Description                                                       | Type        | Required |
| ------------- | ----------------------------------------------------------------- | ----------- | -------- |
| product_name  | Product name for the resource being deployed                      | string      | Yes      |
| feature_name  | Feature name for the resource being deployed                      | string      | Yes      |
| business_unit | Business Unit for the resource being deployed                     | string      | Yes      |
| environment   | Environment for the resource being deployed (dev, qa, prod, core) | string      | Yes      |
| optional_tags | Map of any non-required tags to include                           | map(string) | No       |

---

## Output

| Name    | Description                                            |
| ------- | ------------------------------------------------------ |
| tag_map | A map containing all tags (both required and optional) |
