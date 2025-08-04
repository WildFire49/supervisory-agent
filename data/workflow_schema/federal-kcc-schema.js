// /src/lib/theme/kcc-master-schema.js

// This file consolidates all KCC workflow and UI schemas into a single master file.

// --- CONSTANTS ---
export const INDIAN_STATES = [
    'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
    'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
    'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram',
    'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu',
    'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal'
  ];
  
  // --- ACTION SCHEMA ---
  // Defines the complete workflow for the KCC application process.
  export const kccActionSchema = [
    {
      "id": "kcc-welcome",
      "stage_name": "KCC Welcome Screen",
      "action_type": "WELCOME_SCREEN",
      "next_success_action_id": "verify-otp",
      "ui_id": "ui_kcc_welcome_001",
      "priority": 1,
      "is_mandatory": true,
      "flow_type": "kcc"
    },
    {
      "id": "verify-otp",
      "stage_name": "Verify OTP",
      "action_type": "OTP_VERIFICATION",
      "next_success_action_id": "aadhar-verification",
      "ui_id": "ui_verify_otp_001",
      "priority": 2,
      "is_mandatory": true,
      "flow_type": "kcc"
    },
    {
      "id": "aadhar-verification",
      "stage_name": "Add Aadhar Number",
      "action_type": "AADHAR_VERIFICATION",
      "next_success_action_id": "applicant-details",
      "ui_id": "ui_aadhar_verification_001",
      "priority": 3,
      "is_mandatory": true,
      "flow_type": "kcc"
    },
    {
      "id": "applicant-details",
      "stage_name": "Capture Applicant Details",
      "action_type": "APPLICANT_DETAILS",
      "next_success_action_id": "customer-photo",
      "ui_id": "ui_applicant_details_001",
      "priority": 4,
      "is_mandatory": true,
      "flow_type": "kcc"
    },
    {
      "id": "customer-photo",
      "stage_name": "Capture Customer Photo",
      "action_type": "PHOTO_CAPTURE",
      "next_success_action_id": "residence-details",
      "ui_id": "ui_customer_photo_001",
      "priority": 5,
      "is_mandatory": true,
      "flow_type": "kcc"
    },
    {
      "id": "residence-details",
      "stage_name": "Capture Residence Details",
      "action_type": "RESIDENCE_DETAILS",
      "next_success_action_id": "bank-master",
      "ui_id": "ui_residence_details_001",
      "priority": 6,
      "is_mandatory": true,
      "flow_type": "kcc"
    },
    {
      "id": "bank-master",
      "stage_name": "Capture Bank Master",
      "action_type": "BANK_MASTER",
      "next_success_action_id": "pan-details",
      "ui_id": "ui_bank_master_001",
      "priority": 7,
      "is_mandatory": true,
      "flow_type": "kcc"
    },
    {
      "id": "pan-details",
      "stage_name": "Capture PAN Card Details",
      "action_type": "PAN_DETAILS",
      "next_success_action_id": "secondary-kyc",
      "ui_id": "ui_pan_details_001",
      "priority": 8,
      "is_mandatory": false,
      "flow_type": "kcc"
    },
    {
      "id": "secondary-kyc",
      "stage_name": "Capture Secondary KYC",
      "action_type": "SECONDARY_KYC",
      "next_success_action_id": "demographics-success",
      "ui_id": "ui_secondary_kyc_001",
      "priority": 9,
      "is_mandatory": true,
      "flow_type": "kcc"
    },
    {
      "id": "demographics-success",
      "stage_name": "Demographics Success",
      "action_type": "SUCCESS_MESSAGE",
      "next_success_action_id": "kcc-details",
      "ui_id": "ui_demographics_success_001",
      "priority": 10,
      "is_mandatory": true,
      "flow_type": "kcc"
    },
    {
      "id": "kcc-details",
      "stage_name": "Capture KCC Details",
      "action_type": "KCC_DETAILS",
      "next_success_action_id": "land-details",
      "ui_id": "ui_kcc_details_001",
      "priority": 11,
      "is_mandatory": true,
      "flow_type": "kcc"
    },
    {
      "id": "land-details",
      "stage_name": "Capture Land Details",
      "action_type": "LAND_DETAILS",
      "next_success_action_id": "kcc-completion",
      "ui_id": "ui_land_details_001",
      "priority": 12,
      "is_mandatory": true,
      "flow_type": "kcc"
    }
  ];
  
  // --- UI SCHEMA ---
  // Defines the UI components for each screen in the KCC workflow.
  export const kccUiSchema = [
    // 1. Welcome Screen
    {
      "id": "ui_kcc_welcome_001",
      "screen_id": "kcc_welcome_screen",
      "ui_components": [
        {
          "id": "kcc_welcome_container",
          "component_type": "Container",
          "properties": { "padding": "24px", "textAlign": "center" },
          "children": [
            {
              "id": "kcc_welcome_title",
              "component_type": "Text",
              "properties": {
                "text": "Welcome to Kisan Credit Card Application",
                "variant": "h4",
                "color": "primary",
                "sx": { "fontWeight": "bold", "mb": 2 }
              }
            },
            {
              "id": "kcc_welcome_subtitle",
              "component_type": "Text",
              "properties": {
                "text": "Apply for agricultural loans with ease",
                "variant": "body1",
                "color": "text.secondary",
                "sx": { "mb": 4 }
              }
            },
            {
              "id": "kcc_start_button",
              "component_type": "Button",
              "properties": {
                "text": "Start Application",
                "variant": "contained",
                "color": "primary",
                "size": "large",
                "action": {
                  "type": "navigate_to",
                  "action_id": "kcc-welcome",
                  "next_success_action_id": "verify-otp"
                }
              }
            }
          ]
        }
      ]
    },
  
    // 2. OTP Verification
    {
      "id": "ui_verify_otp_001",
      "screen_id": "verify_otp_screen",
      "ui_components": [
        {
          "id": "otp_container",
          "component_type": "Container",
          "properties": { "padding": "24px" },
          "children": [
            {
              "id": "otp_title",
              "component_type": "Text",
              "properties": {
                "text": "Verify OTP",
                "variant": "h4",
                "color": "primary",
                "sx": { "fontWeight": "bold", "mb": 2, "textAlign": "center" }
              }
            },
            {
              "id": "otp_message",
              "component_type": "Text",
              "properties": {
                "text": "We have sent OTP to {{$mobileNumber}}",
                "variant": "body1",
                "sx": { "mb": 3, "textAlign": "center" }
              }
            },
            {
              "id": "otp_input",
              "component_type": "OTPInput",
              "properties": {
                "label": "Enter 4-digit OTP",
                "length": 4,
                "required": true,
                "sx": { "mb": 3 }
              }
            },
            {
              "id": "verify_otp_button",
              "component_type": "Button",
              "properties": {
                "text": "Verify",
                "variant": "contained",
                "color": "primary",
                "fullWidth": true,
                "action": {
                  "type": "submit_form",
                  "action_id": "verify-otp",
                  "next_success_action_id": "aadhar-verification"
                }
              }
            }
          ]
        }
      ]
    },
  
    // 3. Aadhar Verification
    {
      "id": "ui_aadhar_verification_001",
      "screen_id": "aadhar_verification_screen",
      "ui_components": [
        {
          "id": "aadhar_container",
          "component_type": "Container",
          "properties": { "padding": "24px" },
          "children": [
            {
              "id": "aadhar_title",
              "component_type": "Text",
              "properties": {
                "text": "Add your Aadhar Number",
                "variant": "h4",
                "color": "primary",
                "sx": { "fontWeight": "bold", "mb": 3 }
              }
            },
            {
              "id": "aadhar_input",
              "component_type": "Input",
              "properties": {
                "label": "Enter your 12 digit Aadhar Number",
                "placeholder": "XXXX XXXX XXXX",
                "type": "text",
                "maxLength": 12,
                "required": true,
                "sx": { "mb": 3 }
              }
            },
            {
              "id": "fingerprint_scanner",
              "component_type": "FingerprintScanner",
              "properties": {
                "label": "Tap to scan with fingerprint",
                "sx": { "mb": 3 }
              }
            },
            {
              "id": "verify_aadhar_button",
              "component_type": "Button",
              "properties": {
                "text": "Verify",
                "variant": "contained",
                "color": "primary",
                "fullWidth": true,
                "action": {
                  "type": "submit_form",
                  "action_id": "aadhar-verification",
                  "next_success_action_id": "applicant-details"
                }
              }
            }
          ]
        }
      ]
    },
  
    // 4. Applicant Details
    {
      "id": "ui_applicant_details_001",
      "screen_id": "applicant_details_screen",
      "ui_components": [
        {
          "id": "applicant_container",
          "component_type": "Container",
          "properties": { "padding": "24px" },
          "children": [
            {
              "id": "applicant_title",
              "component_type": "Text",
              "properties": {
                "text": "Capture Applicant Details",
                "variant": "h4",
                "color": "primary",
                "sx": { "fontWeight": "bold", "mb": 3 }
              }
            },
            {
              "id": "full_name_input",
              "component_type": "Input",
              "properties": {
                "label": "Full Name",
                "placeholder": "Enter your full name",
                "required": true,
                "sx": { "mb": 2 }
              }
            },
            {
              "id": "dob_input",
              "component_type": "DatePicker",
              "properties": {
                "label": "Date of Birth",
                "required": true,
                "sx": { "mb": 2 }
              }
            },
            {
              "id": "gender_selector",
              "component_type": "Selector",
              "properties": {
                "label": "Gender",
                "options": ["Male", "Female", "Others"],
                "required": true,
                "sx": { "mb": 2 }
              }
            },
            {
              "id": "father_name_input",
              "component_type": "Input",
              "properties": {
                "label": "Father's Name",
                "placeholder": "Enter father's name",
                "required": true,
                "sx": { "mb": 2 }
              }
            },
            {
              "id": "mother_name_input",
              "component_type": "Input",
              "properties": {
                "label": "Mother's Name",
                "placeholder": "Enter mother's name",
                "required": true,
                "sx": { "mb": 2 }
              }
            },
            {
              "id": "marital_status_selector",
              "component_type": "Selector",
              "properties": {
                "label": "Marital Status",
                "options": ["Married", "Single", "NA"],
                "required": true,
                "sx": { "mb": 2 }
              }
            },
            {
              "id": "qualification_input",
              "component_type": "Input",
              "properties": {
                "label": "Qualification",
                "placeholder": "Enter your qualification",
                "required": true,
                "sx": { "mb": 3 }
              }
            },
            {
              "id": "submit_applicant_button",
              "component_type": "Button",
              "properties": {
                "text": "Continue",
                "variant": "contained",
                "color": "primary",
                "fullWidth": true,
                "action": {
                  "type": "submit_form",
                  "action_id": "applicant-details",
                  "next_success_action_id": "customer-photo"
                }
              }
            }
          ]
        }
      ]
    },
  
    // 5. Customer Photo
    {
      "id": "ui_customer_photo_001",
      "screen_id": "customer_photo_screen",
      "ui_components": [
        {
          "id": "photo_container",
          "component_type": "Container",
          "properties": { "padding": "24px", "textAlign": "center" },
          "children": [
            {
              "id": "photo_title",
              "component_type": "Text",
              "properties": {
                "text": "Capture Customer Photo",
                "variant": "h4",
                "color": "primary",
                "sx": { "fontWeight": "bold", "mb": 3 }
              }
            },
            {
              "id": "customer_photo_capture",
              "component_type": "ImageCapture",
              "properties": {
                "label": "Take Photo",
                "required": true,
                "sx": { "mb": 3 }
              }
            },
            {
              "id": "continue_photo_button",
              "component_type": "Button",
              "properties": {
                "text": "Continue",
                "variant": "contained",
                "color": "primary",
                "fullWidth": true,
                "action": {
                  "type": "submit_form",
                  "action_id": "customer-photo",
                  "next_success_action_id": "residence-details"
                }
              }
            }
          ]
        }
      ]
    },
  
    // 6. Residence Details
    {
      "id": "ui_residence_details_001",
      "screen_id": "residence_details_screen",
      "ui_components": [
        {
          "id": "residence_container",
          "component_type": "Container",
          "properties": { "padding": "24px" },
          "children": [
            {
              "id": "residence_title",
              "component_type": "Text",
              "properties": {
                "text": "Capture Residence Details",
                "variant": "h4",
                "color": "primary",
                "sx": { "fontWeight": "bold", "mb": 2 }
              }
            },
            {
              "id": "kyc_address_subtitle",
              "component_type": "Text",
              "properties": {
                "text": "KYC Address",
                "variant": "h6",
                "sx": { "fontWeight": "bold", "mb": 2 }
              }
            },
            {
              "id": "house_number_input",
              "component_type": "Input",
              "properties": {
                "label": "House Number",
                "placeholder": "Enter house number",
                "required": true,
                "sx": { "mb": 2 }
              }
            },
            {
              "id": "street_input",
              "component_type": "Input",
              "properties": {
                "label": "Street",
                "placeholder": "Enter street name",
                "required": true,
                "sx": { "mb": 2 }
              }
            },
            {
              "id": "locality_input",
              "component_type": "Input",
              "properties": {
                "label": "Locality",
                "placeholder": "Enter locality",
                "required": true,
                "sx": { "mb": 2 }
              }
            },
            {
              "id": "vtc_input",
              "component_type": "Input",
              "properties": {
                "label": "VTC",
                "placeholder": "Enter VTC",
                "required": true,
                "sx": { "mb": 2 }
              }
            }
          ]
        }
      ]
    },
  
    // 7. Bank Master
    {
      "id": "ui_bank_master_001",
      "screen_id": "bank_master_screen",
      "ui_components": [
        {
          "id": "bank_container",
          "component_type": "Container",
          "properties": { "padding": "24px" },
          "children": [
            {
              "id": "bank_title",
              "component_type": "Text",
              "properties": {
                "text": "Capture Bank Master",
                "variant": "h4",
                "color": "primary",
                "sx": { "fontWeight": "bold", "mb": 3 }
              }
            },
            {
              "id": "country_selector",
              "component_type": "Selector",
              "properties": {
                "label": "Country",
                "options": ["India", "USA", "UK", "Canada", "Australia"],
                "defaultValue": "India",
                "required": true,
                "sx": { "mb": 2 }
              }
            },
            {
              "id": "bank_state_selector",
              "component_type": "Selector",
              "properties": {
                "label": "State",
                "options": INDIAN_STATES,
                "required": true,
                "sx": { "mb": 2 }
              }
            },
            {
              "id": "city_input",
              "component_type": "Input",
              "properties": {
                "label": "City",
                "placeholder": "Enter city name",
                "required": true,
                "sx": { "mb": 2 }
              }
            },
            {
              "id": "district_input",
              "component_type": "Input",
              "properties": {
                "label": "District",
                "placeholder": "Enter district name",
                "required": true,
                "sx": { "mb": 3 }
              }
            },
            {
              "id": "continue_bank_button",
              "component_type": "Button",
              "properties": {
                "text": "Continue",
                "variant": "contained",
                "color": "primary",
                "fullWidth": true,
                "action": {
                  "type": "submit_form",
                  "action_id": "bank-master",
                  "next_success_action_id": "pan-details"
                }
              }
            }
          ]
        }
      ]
    },
  
    // 8. PAN Details
    {
      "id": "ui_pan_details_001",
      "screen_id": "pan_details_screen",
      "ui_components": [
        {
          "id": "pan_container",
          "component_type": "Container",
          "properties": { "padding": "24px" },
          "children": [
            {
              "id": "pan_title",
              "component_type": "Text",
              "properties": {
                "text": "Capture PAN Card Details",
                "variant": "h4",
                "color": "primary",
                "sx": { "fontWeight": "bold", "mb": 3 }
              }
            },
            {
              "id": "pan_available_checkbox",
              "component_type": "Checkbox",
              "properties": {
                "label": "Is PAN Available?",
                "required": true,
                "sx": { "mb": 2 }
              }
            },
            {
              "id": "pan_number_input",
              "component_type": "Input",
              "properties": {
                "label": "PAN Number",
                "placeholder": "Enter PAN number (AAAAA9999A)",
                "maxLength": 10,
                "sx": { "mb": 2 }
              }
            },
            {
              "id": "pan_name_input",
              "component_type": "Input",
              "properties": {
                "label": "Customer name as per PAN",
                "placeholder": "Enter name as per PAN",
                "sx": { "mb": 2 }
              }
            },
            {
              "id": "pan_image_upload",
              "component_type": "FileUpload",
              "properties": {
                "label": "Upload PAN Image",
                "accept": "image/*",
                "sx": { "mb": 3 }
              }
            },
            {
              "id": "continue_pan_button",
              "component_type": "Button",
              "properties": {
                "text": "Continue",
                "variant": "contained",
                "color": "primary",
                "fullWidth": true,
                "action": {
                  "type": "submit_form",
                  "action_id": "pan-details",
                  "next_success_action_id": "secondary-kyc"
                }
              }
            }
          ]
        }
      ]
    },
  
    // 9. Secondary KYC
    {
      "id": "ui_secondary_kyc_001",
      "screen_id": "secondary_kyc_screen",
      "ui_components": [
        {
          "id": "secondary_kyc_container",
          "component_type": "Container",
          "properties": { "padding": "24px" },
          "children": [
            {
              "id": "secondary_kyc_title",
              "component_type": "Text",
              "properties": {
                "text": "Capture Secondary KYC",
                "variant": "h4",
                "color": "primary",
                "sx": { "fontWeight": "bold", "mb": 2 }
              }
            },
            {
              "id": "add_kyc_subtitle",
              "component_type": "Text",
              "properties": {
                "text": "Add KYC",
                "variant": "h6",
                "sx": { "fontWeight": "bold", "mb": 2 }
              }
            },
            {
              "id": "kyc_type_selector",
              "component_type": "Selector",
              "properties": {
                "label": "Type",
                "options": ["Passport", "Voter ID", "Driver's License"],
                "required": true,
                "sx": { "mb": 2 }
              }
            },
            {
              "id": "kyc_document_number_input",
              "component_type": "Input",
              "properties": {
                "label": "KYC Document Number",
                "placeholder": "Enter document number",
                "required": true,
                "sx": { "mb": 2 }
              }
            },
            {
              "id": "kyc_document_photos",
              "component_type": "FileUpload",
              "properties": {
                "label": "Capture 2 Document Photos",
                "accept": "image/*",
                "multiple": true,
                "maxFiles": 2,
                "required": true,
                "sx": { "mb": 3 }
              }
            },
            {
              "id": "submit_kyc_button",
              "component_type": "Button",
              "properties": {
                "text": "Submit",
                "variant": "contained",
                "color": "primary",
                "fullWidth": true,
                "action": {
                  "type": "submit_form",
                  "action_id": "secondary-kyc",
                  "next_success_action_id": "demographics-success"
                }
              }
            }
          ]
        }
      ]
    },
  
    // 10. Demographics Success
    {
      "id": "ui_demographics_success_001",
      "screen_id": "demographics_success_screen",
      "ui_components": [
        {
          "id": "success_container",
          "component_type": "Container",
          "properties": { "padding": "24px", "textAlign": "center" },
          "children": [
            {
              "id": "success_title",
              "component_type": "Text",
              "properties": {
                "text": "Demographics Details Submitted Successfully!",
                "variant": "h4",
                "color": "success.main",
                "sx": { "fontWeight": "bold", "mb": 3 }
              }
            },
            {
              "id": "success_message",
              "component_type": "Text",
              "properties": {
                "text": "Your personal information has been successfully recorded. Let's proceed to KCC details.",
                "variant": "body1",
                "sx": { "mb": 4 }
              }
            },
            {
              "id": "continue_success_button",
              "component_type": "Button",
              "properties": {
                "text": "Continue to KCC Details",
                "variant": "contained",
                "color": "primary",
                "size": "large",
                "action": {
                  "type": "navigate_to",
                  "action_id": "demographics-success",
                  "next_success_action_id": "kcc-details"
                }
              }
            }
          ]
        }
      ]
    },
  
    // 11. KCC Details
    {
      "id": "ui_kcc_details_001",
      "screen_id": "kcc_details_screen",
      "ui_components": [
        {
          "id": "kcc_details_container",
          "component_type": "Container",
          "properties": { "padding": "24px" },
          "children": [
            {
              "id": "kcc_details_title",
              "component_type": "Text",
              "properties": {
                "text": "Capture KCC Details",
                "variant": "h4",
                "color": "primary",
                "sx": { "fontWeight": "bold", "mb": 3 }
              }
            },
            {
              "id": "customer_list",
              "component_type": "CustomerList",
              "properties": {
                "sx": { "mb": 3 }
              }
            },
            {
              "id": "continue_kcc_button",
              "component_type": "Button",
              "properties": {
                "text": "Continue to Land Details",
                "variant": "contained",
                "color": "primary",
                "fullWidth": true,
                "action": {
                  "type": "submit_form",
                  "action_id": "kcc-details",
                  "next_success_action_id": "land-details"
                }
              }
            }
          ]
        }
      ]
    },
  
    // 12. Land Details
    {
      "id": "ui_land_details_001",
      "screen_id": "land_details_screen",
      "ui_components": [
        {
          "id": "land_container",
          "component_type": "Container",
          "properties": { "padding": "24px" },
          "children": [
            {
              "id": "land_title",
              "component_type": "Text",
              "properties": {
                "text": "Capture Land Details",
                "variant": "h4",
                "color": "primary",
                "sx": { "fontWeight": "bold", "mb": 3 }
              }
            },
            {
              "id": "land_state_selector",
              "component_type": "Selector",
              "properties": {
                "label": "State",
                "options": INDIAN_STATES,
                "required": true,
                "sx": { "mb": 2 }
              }
            },
            {
              "id": "land_district_input",
              "component_type": "Input",
              "properties": {
                "label": "District",
                "placeholder": "Enter district",
                "required": true,
                "sx": { "mb": 2 }
              }
            },
            {
              "id": "village_input",
              "component_type": "Input",
              "properties": {
                "label": "Village",
                "placeholder": "Enter village name",
                "required": true,
                "sx": { "mb": 2 }
              }
            },
            {
              "id": "taluk_input",
              "component_type": "Input",
              "properties": {
                "label": "Taluk",
                "placeholder": "Enter taluk",
                "required": true,
                "sx": { "mb": 2 }
              }
            },
            {
              "id": "survey_number_input",
              "component_type": "Input",
              "properties": {
                "label": "Survey Number",
                "placeholder": "Enter survey number",
                "required": true,
                "sx": { "mb": 3 }
              }
            },
            {
              "id": "submit_land_button",
              "component_type": "Button",
              "properties": {
                "text": "Submit Application",
                "variant": "contained",
                "color": "primary",
                "fullWidth": true,
                "action": {
                  "type": "submit_form",
                  "action_id": "land-details",
                  "next_success_action_id": "kcc-completion"
                }
              }
            }
          ]
        }
      ]
    }
  ];
  