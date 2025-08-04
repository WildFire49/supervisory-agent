// Complete Customer Onboarding Workflow Schema
// This file defines the complete workflow structure for customer onboarding

/**
 * Function to get workflow response based on current action ID
 * This is what the supervisor agent will call to get the appropriate UI schema
 */
export const getWorkflowResponseForAction = (actionId, sessionData = {}) => {
  const responses = {
    "welcome": {
      success: true,
      current_action: {
        action_id: "welcome",
        stage_name: "Welcome Screen",
        action_type: "WELCOME_SCREEN",
        priority: 1,
        is_mandatory: true,
        flow_type: "onboarding",
        description: "Initial welcome screen for new customer onboarding"
      },
      ui_schema: {
        id: "ui_welcome_screen_001",
        session_id: sessionData.session_id || "session_12345",
        screen_id: "welcome_screen",
        ui_components: [{
          id: "welcome_container",
          component_type: "column",
          properties: {
            padding: "24dp",
            background_color: "#FFFFFF",
            vertical_arrangement: "center",
            horizontal_alignment: "center"
          },
          children: [{
            id: "welcome_text",
            component_type: "text",
            properties: {
              text: "Welcome to MiFix Customer Onboarding",
              text_size: "28sp",
              text_color: "#1976d2",
              text_style: "bold",
              text_align: "center",
              margin_bottom: "16dp"
            }
          }, {
            id: "subtitle_text",
            component_type: "text",
            properties: {
              text: "Let's get you started with a quick onboarding process",
              text_size: "16sp",
              text_color: "#666666",
              text_align: "center",
              margin_bottom: "32dp"
            }
          }, {
            id: "get_started_button",
            component_type: "button",
            properties: {
              text: "Get Started",
              background_color: "#1976d2",
              text_color: "#FFFFFF",
              text_size: "16sp",
              corner_radius: "8dp",
              padding: "16dp",
              action: {
                type: "navigate_to",
                action_id: "welcome",
                next_success_action_id: "video-consent"
              }
            }
          }]
        }]
      },
      navigation: {
        next_success_action_id: "video-consent",
        next_err_action_id: "welcome",
        can_skip: false
      },
      session_data: {
        session_id: sessionData.session_id || "session_12345",
        customer_id: sessionData.customer_id || null,
        flow_type: "onboarding",
        current_step: 1,
        total_steps: 7,
        ...sessionData
      }
    },
    "mobile-verification": {
      success: true,
      current_action: {
        action_id: "mobile-verification",
        stage_name: "Mobile Number Verification",
        action_type: "MOBILE_VERIFICATION_SCREEN",
        priority: 4,
        is_mandatory: true,
        flow_type: "onboarding",
        validation_required: true,
        description: "Collect and verify customer's mobile number"
      },
      ui_schema: {
        id: "ui_mobile_verification_001",
        session_id: sessionData.session_id || "session_12345",
        screen_id: "mobile_verification_screen",
        ui_components: [{
          id: "mobile_container",
          component_type: "column",
          properties: { padding: "24dp" },
          children: [{
            id: "mobile_title",
            component_type: "text",
            properties: {
              text: "Mobile Number Verification",
              text_size: "24sp",
              text_style: "bold",
              margin_bottom: "16dp"
            }
          }, {
            id: "mobile_input",
            component_type: "text_input",
            properties: {
              hint: "Enter your 10-digit mobile number",
              input_type: "phone",
              max_length: 10,
              margin_bottom: "24dp",
              field_name: "mobile_number",
              validation: {
                required: true,
                pattern: "^[0-9]{10}$",
                custom_error: "Please enter a valid 10-digit mobile number"
              }
            }
          }, {
            id: "send_otp_button",
            component_type: "button",
            properties: {
              text: "Send OTP",
              background_color: "#4CAF50",
              text_color: "#FFFFFF",
              action: {
                type: "submit_form",
                endpoint: "/api/send-mobile-otp",
                method: "POST",
                collect_fields: ["mobile_input"],
                action_id: "mobile-verification",
                next_success_action_id: "otp-verification"
              }
            }
          }]
        }]
      },
      navigation: {
        next_success_action_id: "otp-verification",
        next_err_action_id: "mobile-verification",
        can_skip: false
      },
      session_data: {
        session_id: sessionData.session_id || "session_12345",
        customer_id: sessionData.customer_id || null,
        flow_type: "onboarding",
        current_step: 4,
        total_steps: 7,
        ...sessionData
      }
    }
  };

  const response = responses[actionId];
  if (!response) {
    throw new Error(`No workflow response found for action: ${actionId}`);
  }

  return response;
};

// Enhanced Action Schema - Backend configurable flow definitions
// Each action defines a stage in the user journey with navigation logic
export const getActionSchema = () => [
    {
        "id": "welcome",
        "stage_name": "Welcome Screen",
        "desc_for_llm": "Simple welcome screen with app name and proceed button, hey, hello, goodmorning, I want to start Onboarding. I want to start journey",
        "action_type": "WELCOME_SCREEN",
        "next_err_action_id": "welcome",
        "next_success_action_id": "video-consent",
        "ui_id": "ui_welcome_screen_001",
        "api_detail_id": null,
        "priority": 1,
        "is_mandatory": true,
        "flow_type": "onboarding"
    },
    {
        "id": "video-consent",
        "stage_name": "Video Consent",
        "desc_for_llm": "Consent screen with video component and a button to capture user agreement after viewing. User wants to wants to give consent for loan and agree to it.",
        "action_type": "VIDEO_CONSENT_SCREEN",
        "next_err_action_id": "video-consent",
        "next_success_action_id": "select-flow",
        "ui_id": "ui_video_consent_001",
        "api_detail_id": "api_video_consent_001",
        "priority": 2,
        "is_mandatory": true,
        "flow_type": "onboarding",
        "validation_required": true
    },
    {
        "id": "select-flow",
        "stage_name": "Select Flow",
        "desc_for_llm": "select either the Onboarding or Collections flow",
        "action_type": "FLOW_SELECTION_SCREEN",
        "next_err_action_id": "select-flow",
        "next_success_action_id": "mobile-verification",
        "ui_id": "ui_select_flow_001",
        "api_detail_id": "api_select_flow_001",
        "priority": 3,
        "is_mandatory": true,
        "flow_type": "both",
        "conditional_next": {
            "onboarding": "mobile-verification",
            "collections": "customer-photo"
        }
    },
    {
        "id": "mobile-verification",
        "stage_name": "Mobile Number Verification",
        "desc_for_llm": "Screen for mobile number verifications and verifying customer's mobile number. Takes 10-digit input and validates. Enter Customer Mobile Number to verify. Mobile number verifications",
        "action_type": "MOBILE_VERIFICATION_SCREEN",
        "next_err_action_id": "mobile-verification",
        "next_success_action_id": "otp-verification",
        "ui_id": "ui_mobile_verification_001",
        "api_detail_id": "api_mobile_verification_001"
    },
    {
        "id": "otp-verification",
        "stage_name": "OTP Verification Screen",
        "desc_for_llm": "Screen for entering OTP sent to user's mobile number. OTP verification screen. Confirm OTP. Validate OTP",
        "action_type": "OTP_VERIFICATION_SCREEN",
        "next_err_action_id": "mobile-verification",
        "next_success_action_id": "customer-photo",
        "ui_id": "ui_otp_verification_001",
        "api_detail_id": "api_otp_verification_001"
    },
    {
        "id": "review-screen",
        "stage_name": "Review Details Screen",
        "desc_for_llm": "Screen for user to review their provided information before submission.",
        "action_type": "REVIEW_SCREEN",
        "next_err_action_id": "review-screen",
        "next_success_action_id": "select-documents",
        "ui_id": "ui_review_screen_001"
    },
    {
        "id": "select-documents",
        "stage_name": "Select Documents",
        "desc_for_llm": "Screen for user to select the documents they have ready.",
        "action_type": "CHECKBOX_LIST_SCREEN",
        "next_err_action_id": "select-documents",
        "next_success_action_id": "customer-photo",
        "ui_id": "ui_select_documents_001"
    },
    {
        "id":"customer-photo",
        "stage_name":"Customer Photo",
        "desc_for_llm":"Screen to upload or capture Customer Photo",
        "action_type":"CUSTOMER_PHOTO_SCREEN",
        "next_err_action_id":"customer-photo",
        "next_success_action_id":"secondry-kyc-document-selector", 
        "ui_id":"ui_customer_photo_001"
    },
    {
        "id": "secondry-kyc-document-selector",
        "stage_name": "Secondary KYC Document Selector",
        "desc_for_llm": "Screen to select a secondary KYC document type from a dropdown.",
        "action_type": "KYC_DOCUMENT_SELECTION_SCREEN",
        "next_err_action_id": "secondry-kyc-document-selector",
        "next_success_action_id": "terms-and-conditions", // End of flow for now
        "ui_id": "ui_secondry_kyc_document_selector_001"
    },
    {
        "id": "terms-and-conditions",
        "stage_name": "Terms and Conditions",
        "desc_for_llm": "Screen to agree to terms and conditions.",
        "action_type": "TERMS_AND_CONDITIONS_SCREEN",
        "next_err_action_id": "terms-and-conditions",
        "next_success_action_id": "location-capture",
        "ui_id": "ui_terms_and_conditions_001"
    },
    {
        "id": "location-capture",
        "stage_name": "Location Consent",
        "desc_for_llm": "Screen to ask the user for their location.",
        "action_type": "LOCATION_CAPTURE_SCREEN",
        "next_err_action_id": "location-capture",
        "next_success_action_id": "review-information",
        "ui_id": "ui_location_capture_001"
    },
    {
        "id": "gender-selection",
        "stage_name": "Gender Selection",
        "desc_for_llm": "Screen for user to select their gender.",
        "action_type": "GENDER_SELECTION_SCREEN",
        "next_err_action_id": "gender-selection",
        "next_success_action_id": "document-checklist",
        "ui_id": "ui_gender_selection_001"
    },
    {
        "id": "document-checklist",
        "stage_name": "Document Checklist",
        "desc_for_llm": "Screen for user to select the documents they have ready.",
        "action_type": "CHECKBOX_LIST_SCREEN",
        "next_err_action_id": "document-checklist",
        "next_success_action_id": "loan-features",
        "ui_id": "ui_document_checklist_001"
    },
    {
        "id": "loan-features",
        "stage_name": "Loan Features",
        "desc_for_llm": "Screen for user to select additional loan features.",
        "action_type": "MULTI_SELECT_GRID_SCREEN",
        "next_err_action_id": "loan-features",
        "next_success_action_id": "document-upload",
        "ui_id": "ui_loan_features_001"
    },
    {
        "id": "document-upload",
        "stage_name": "Document Upload",
        "desc_for_llm": "Screen for user to upload their selected KYC document.",
        "action_type": "FILE_UPLOAD_SCREEN",
        "next_err_action_id": "document-upload",
        "next_success_action_id": "document-verification",
        "ui_id": "ui_document_upload_001"
    },
    {
        "id": "document-verification",
        "stage_name": "Document Verification",
        "desc_for_llm": "Screen to show the status of document verification.",
        "action_type": "STATUS_NOTIFICATION_SCREEN",
        "next_err_action_id": "document-verification",
        "next_success_action_id": "loan-summary",
        "ui_id": "ui_document_verification_001"
    },
    {
        "id": "loan-summary",
        "stage_name": "Loan Summary",
        "desc_for_llm": "Screen to display a summary of the loan details.",
        "action_type": "DASHBOARD_METRICS_SCREEN",
        "next_err_action_id": "loan-summary",
        "next_success_action_id": "live-photo-capture",
        "ui_id": "ui_loan_summary_001"
    },
    {
        "id": "review-information",
        "stage_name": "Review Information",
        "desc_for_llm": "Screen for user to review the information they have provided.",
        "action_type": "REVIEW_INFORMATION_SCREEN",
        "next_err_action_id": "review-information",
        "next_success_action_id": "loan-summary",
        "ui_id": "ui_review_information_001"
    },
    {
        "id": "application-review",
        "stage_name": "Application Review",
        "desc_for_llm": "Screen for user to review their complete application before submission.",
        "action_type": "TEXT_REVIEW_SCREEN",
        "next_err_action_id": "application-review",
        "next_success_action_id": "gender-selection",
        "ui_id": "ui_application_review_001",
        "confirmation": {
            "title": "Final Submission",
            "message": "You are about to submit your application. This action cannot be undone. Are you sure you want to proceed?"
        }
    },
    {
        "id": "live-photo-capture",
        "stage_name": "Live Photo Capture",
        "desc_for_llm": "Screen for user to capture a live photo using the device camera.",
        "action_type": "CAMERA_MODAL_SCREEN",
        "next_err_action_id": "live-photo-capture",
        "next_success_action_id": "application-review",
        "ui_id": "ui_live_photo_capture_001"
    },
    {
        "id": "onboarding-complete",
        "stage_name": "Onboarding Complete",
        "desc_for_llm": "Final screen to notify the user of successful onboarding.",
        "action_type": "SUCCESS_NOTIFICATION_SCREEN",
        "next_err_action_id": null,
        "next_success_action_id": null, // End of flow
        "ui_id": "ui_onboarding_complete_001"
    }
];

export const getUiSchema = () => [
    {
        "id": "ui_welcome_screen_001",
        "ui_components": [
            {
                "id": "main_container",
                "component_type": "column",
                "properties": {
                    "alignItems": "center",
                    "justifyContent": "center"
                },
                "children": [
                    {
                        "id": "avatar_image",
                        "component_type": "image",
                        "properties": {
                            "uri": "/ai-chatbot.png",
                            "width": "162dp",
                            "height": "162dp",
                            "align": "center",
                            "border_radius": "30%"
                        }
                    },
                    {
                        "id": "welcome_text",
                        "component_type": "text",
                        "properties": {
                            "text": "Welcome to MiFiX AI",
                            "text_size": "28sp",
                            "text_style": "bold",
                            "color": "#2563EB",
                            "margin_bottom": "16dp",
                            "text_align": "center"
                        }
                    },
                    {
                        "id": "welcome_description",
                        "component_type": "text",
                        "properties": {
                            "text": "I'm here to help you with any questions or queries you might have. Feel free to ask me anything!",
                            "text_size": "16sp",
                            "margin_bottom": "32dp",
                            "text_align": "center",
                            "color": "#4B5563"
                        }
                    },
                    {
                        "id": "proceed_button",
                        "component_type": "button",
                        "properties": {
                            "text": "Get Started",
                            "action": {
                                "type": "next_screen",
                                "action_id": "welcome"
                            }
                        }
                    }
                ]
            }
        ]
    },
    {
        "id": "ui_select_flow_001",
        "ui_components": [
            {
                "id": "main_container",
                "component_type": "column",
                "children": [
                    {
                        "id": "select_flow_text",
                        "component_type": "text",
                        "properties": {
                            "text": "Please select a flow to continue.",
                            "text_size": "18sp",
                            "margin_bottom": "24dp"
                        }
                    },
                    {
                        "id": "onboarding_button",
                        "component_type": "button",
                        "properties": {
                            "text": "Start Onboarding",
                            "margin_bottom": "12dp",
                            "action": {
                                "type": "next_screen",
                                "action_id": "select-flow"
                            }
                        }
                    }
                ]
            }
        ]
    },
    {
        "id": "ui_video_consent_001",
        "ui_components": [
            {
                "id": "main_container",
                "component_type": "column",
                "children": [
                    {
                        "id": "video_player",
                        "component_type": "video",
                        "properties": {
                          "uri": "/assets/Marathi.mp4",
                          "margin_bottom": "16dp",
                          "autoplay": false,
                          "controls": true,
                          "aspect_ratio": "16/9",
                          "corner_radius": "12dp"
                        }
                      },
                    {
                        "id": "consent_button",
                        "component_type": "button",
                        "properties": {
                            "text": "I Agree",
                            "action": {
                                "type": "next_screen",
                                "action_id": "video-consent"
                            }
                        }
                    }
                ]
            }
        ]
    },
    {
        "id": "ui_mobile_verification_001",
        "ui_components": [
            {
                "id": "main_container",
                "component_type": "column",
                "children": [
                    {
                        "id": "mobile_input",
                        "component_type": "text_input",
                        "properties": {
                            "hint": "Enter Mobile No.",
                            "input_type": "number",
                            "margin_bottom": "16dp"
                        }
                    },
                    {
                        "id": "verify_button",
                        "component_type": "button",
                        "properties": {
                            "text": "Verify",
                            "action": {
                                "type": "next_screen",
                                "action_id": "mobile-verification"
                            }
                        }
                    }
                ]
            }
        ]
    },
    {
        "id": "ui_otp_verification_001",
        "ui_components": [
            {
                "id": "main_container",
                "component_type": "column",
                "children": [
                    {
                        "id": "otp_input",
                        "component_type": "text_input",
                        "properties": {
                            "hint": "Enter OTP",
                            "input_type": "otp",
                            "length": 6,
                            "margin_bottom": "16dp"
                        }
                    },
                    {
                        "id": "submit_otp_button",
                        "component_type": "button",
                        "properties": {
                            "text": "Submit OTP",
                            "action": {
                                "type": "next_screen",
                                "action_id": "otp-verification"
                            }
                        }
                    }
                ]
            }
        ]
    },
    {
        "id": "ui_customer_photo_001",
        "ui_components": [
            {
                "id": "main_container",
                "component_type": "column",
                "properties": {
                    "alignItems": "center"
                },
                "children": [
                    {
                        "id": "customer_photo_capture",
                        "component_type": "image_capture",
                        "properties": {
                            "title": "Upload Customer Photo",
                            "instructions": "Please provide a clear photo.",
                            "margin_bottom": "16dp"
                        }
                    },
                    {
                        "id": "submit_photo_button",
                        "component_type": "button",
                        "properties": {
                            "text": "Submit Photo",
                            "action": {
                                "type": "next_screen",
                                "action_id": "customer-photo"
                            }
                        }
                    }
                ]
            }
        ]
    },
    {
        "id": "ui_secondry_kyc_document_selector_001",
        "ui_components": [
            {
                "id": "main_container",
                "component_type": "column",
                "properties": {
                    "padding": "16dp",
                    "width": "100%",
                    "alignItems": "center"
                },
                "children": [
                    {
                        "id": "kyc_selector",
                        "component_type": "selector",
                        "properties": {
                            "label": "Select Document Type",
                            "width": "100%",
                            "minWidth": "280dp",
                            "options": [
                                { "value": "aadhar", "label": "Aadhar Card" },
                                { "value": "drivers_license", "label": "Driver's License" },
                                { "value": "passport", "label": "Passport" }
                            ],
                            "margin_bottom": "16dp"
                        }
                    },
                    {
                        "id": "submit_kyc_button",
                        "component_type": "button",
                        "properties": {
                            "text": "Continue",
                            "action": {
                                "type": "next_screen",
                                "action_id": "secondry-kyc-document-selector"
                            }
                        }
                    }
                ]
            }
        ]
    },
    {
        "id": "ui_terms_and_conditions_001",
        "ui_components": [
            {
                "id": "main_container",
                "component_type": "column",
                "children": [
                    {
                        "id": "terms_checkbox",
                        "component_type": "checkbox",
                        "properties": {
                            "label": "I agree to the Terms and Conditions",
                            "margin_bottom": "16dp"
                        }
                    },
                    {
                        "id": "submit_terms_button",
                        "component_type": "button",
                        "properties": {
                            "text": "Finish Onboarding",
                            "action": {
                                "type": "next_screen",
                                "action_id": "terms-and-conditions"
                            }
                        }
                    }
                ]
            }
        ]
    },
    {
        "id": "ui_gender_selection_001",
        "ui_components": [
            {
                "id": "main_container",
                "component_type": "column",
                "children": [
                    {
                        "id": "gender_radio_group",
                        "component_type": "radio_group",
                        "properties": {
                            "label": "Please select your gender",
                            "options": [
                                { "value": "male", "label": "Male" },
                                { "value": "female", "label": "Female" },
                                { "value": "other", "label": "Other" }
                            ]
                        }
                    },
                    {
                        "id": "submit_gender_button",
                        "component_type": "button",
                        "properties": {
                            "text": "Complete",
                            "action": {
                                "type": "next_screen",
                                "action_id": "gender-selection"
                            }
                        }
                    }
                ]
            }
        ]
    },
    {
        "id": "ui_document_upload_001",
        "ui_components": [
            {
                "id": "main_container",
                "component_type": "column",
                "children": [
                    {
                        "id": "document_uploader",
                        "component_type": "file_upload",
                        "properties": {
                            "label": "Upload Your Document"
                        }
                    },
                    {
                        "id": "submit_document_button",
                        "component_type": "button",
                        "properties": {
                            "text": "Finish",
                            "action": {
                                "type": "next_screen",
                                "action_id": "document-upload"
                            }
                        }
                    }
                ]
            }
        ]
    },
    {
        "id": "ui_onboarding_complete_001",
        "ui_components": [
            {
                "id": "success_notification_main",
                "component_type": "success_notification",
                "properties": {
                    "title": "Onboarding Complete!",
                    "message": "Thank you for joining us. You can now explore all our features."
                }
            }
        ]
    },
    {
        "id": "ui_location_capture_001",
        "ui_components": [
            {
                "id": "location_capture_main",
                "component_type": "location_capture",
                "properties": {
                    "title": "Share Your Location",
                    "instructions": "To continue, please share your current location."
                }
            },
            {
                "id": "submit_location_button",
                "component_type": "button",
                "properties": {
                    "text": "Continue",
                    "action": {
                        "type": "next_screen",
                        "action_id": "location-capture"
                    }
                }
            }
        ]
    },
    {
        "id": "ui_review_information_001",
        "ui_components": [
            {
                "id": "review_text",
                "component_type": "read_only_text",
                "properties": {
                    "title": "Please Review Your Details",
                    "content": "- Name: John Doe\n- Mobile: +91 98765 43210\n- Location: Captured Successfully\n\nPlease ensure all details are correct before proceeding."
                }
            },
            {
                "id": "submit_review_button",
                "component_type": "button",
                "properties": {
                    "text": "Confirm & Continue",
                    "action": {
                        "type": "next_screen",
                        "action_id": "review-information"
                    }
                }
            }
        ]
    },
    {
        "id": "ui_loan_summary_001",
        "ui_components": [
            {
                "id": "loan_summary_metrics",
                "component_type": "dashboard_metrics",
                "properties": {
                    "title": "Your Loan Summary",
                    "metrics": [
                        { "label": "Loan Amount", "value": "₹50,000" },
                        { "label": "Tenure", "value": "12 Months" },
                        { "label": "Interest Rate", "value": "13.5%" },
                        { "label": "Monthly EMI", "value": "₹4,478" }
                    ]
                }
            },
            {
                "id": "submit_loan_summary_button",
                "component_type": "button",
                "properties": {
                    "text": "Accept & Proceed",
                    "action": {
                        "type": "next_screen",
                        "action_id": "loan-summary"
                    }
                }
            }
        ]
    },
    {
        "id": "ui_live_photo_capture_001",
        "ui_components": [
            {
                "id": "live_photo_modal",
                "component_type": "camera_modal",
                "properties": {
                    "title": "Live Selfie Verification"
                }
            },
            {
                "id": "submit_live_photo_button",
                "component_type": "button",
                "properties": {
                    "text": "Continue",
                    "action": {
                        "type": "next_screen",
                        "action_id": "live-photo-capture"
                    }
                }
            }
        ]
    },
    {
        "id": "ui_application_review_001",
        "ui_components": [
            {
                "id": "application_review_panel",
                "component_type": "text_review_panel",
                "properties": {
                    "title": "Confirm Your Application",
                    "content": "**Personal Details**\nName: John Doe\nMobile: +91 98765 43210\n\n**Loan Details**\nAmount: ₹50,000\nTenure: 12 Months\n\n**Documents**\n- Aadhar Card: uploaded\n- Selfie: captured\n\nBy clicking 'Submit Application', you agree to all terms and conditions."
                }
            },
            {
                "id": "submit_application_button",
                "component_type": "button",
                "properties": {
                    "text": "Submit Application",
                    "action": {
                        "type": "next_screen",
                        "action_id": "application-review"
                    }
                }
            }
        ]
    },
    {
        "id": "ui_document_checklist_001",
        "ui_components": [
            {
                "id": "doc_checklist",
                "component_type": "checkbox_list",
                "properties": {
                    "title": "Which documents are you providing?",
                    "options": [
                        { "label": "PAN Card", "value": "pan" },
                        { "label": "Aadhar Card", "value": "aadhar" },
                        { "label": "Latest Bank Statement", "value": "bank_statement" },
                        { "label": "Salary Slips (3 months)", "value": "salary_slips" }
                    ]
                }
            },
            {
                "id": "submit_docs_button",
                "component_type": "button",
                "properties": {
                    "text": "Continue",
                    "action": {
                        "type": "next_screen",
                        "action_id": "document-checklist"
                    }
                }
            }
        ]
    },
    {
        "id": "ui_loan_features_001",
        "ui_components": [
            {
                "id": "feature_grid",
                "component_type": "multi_select_grid",
                "properties": {
                    "title": "Enhance Your Loan",
                    "options": [
                        { "label": "Credit Insurance", "value": "insurance", "description": "Protect your loan against unforeseen events." },
                        { "label": "Flexible Repayment", "value": "flexi_repay", "description": "Pay more when you can, less when you can't." },
                        { "label": "Loan Top-Up", "value": "top_up", "description": "Get additional funds on your existing loan." },
                        { "label": "Zero Prepayment Charges", "value": "no_prepayment_fee", "description": "Pay off your loan early without any penalty." }
                    ]
                }
            },
            {
                "id": "submit_features_button",
                "component_type": "button",
                "properties": {
                    "text": "Continue",
                    "action": {
                        "type": "next_screen",
                        "action_id": "loan-features"
                    }
                }
            }
        ]
    },
    {
        "id": "ui_document_upload_001",
        "ui_components": [
            {
                "id": "doc_upload_component",
                "component_type": "file_upload",
                "properties": {
                    "title": "Upload Your Document",
                    "label": "Click or drag to upload"
                }
            },
            {
                "id": "submit_uploaded_doc_button",
                "component_type": "button",
                "properties": {
                    "text": "Submit Document",
                    "action": {
                        "type": "next_screen",
                        "action_id": "document-upload"
                    }
                }
            }
        ]
    },
    {
        "id": "ui_document_verification_001",
        "ui_components": [
            {
                "id": "verification_status",
                "component_type": "status_notification",
                "properties": {
                    "severity": "info",
                    "title": "Verification in Progress",
                    "message": "We're currently verifying your documents. This should only take a moment. We'll automatically proceed once it's complete."
                }
            },
            {
                "id": "auto_proceed_action",
                "component_type": "action",
                "properties": {
                    "trigger_delay": 3000,
                    "action": {
                        "type": "next_screen",
                        "action_id": "document-verification"
                    }
                }
            }
        ]
    },
    {
        "id": "ui_emi_screen_001",
        "ui_components": [
            {
                "id": "main_container",
                "component_type": "column",
                "children": [
                    {
                        "id": "emi_panel",
                        "component_type": "emi_display_panel",
                        "properties": {
                            "title": "Your Loan Details",
                            "emiDetails": {
                                "principal": 500000,
                                "interestRate": 12.5,
                                "tenure": 60,
                                "emi": 11249,
                                "totalInterest": 174940,
                                "totalAmount": 674940
                            }
                        }
                    },
                    {
                        "id": "continue_button",
                        "component_type": "button",
                        "properties": {
                            "text": "Continue",
                            "action": {
                                "type": "next_screen",
                                "action_id": "customer-photo"
                            }
                        }
                    }
                ]
            }
        ]
    },
    {
        "id": "ui_review_screen_001",
        "ui_components": [
            {
                "id": "main_container",
                "component_type": "column",
                "children": [
                    {
                        "id": "review_panel",
                        "component_type": "review_panel",
                        "properties": {
                            "title": "Confirm Your Details",
                            "reviewItems": [
                                { "label": "Mobile Number", "value": "+91 8511044804" },
                                { "label": "Customer Photo", "value": "photo_uploaded.jpg" },
                                { "label": "Selected Flow", "value": "Onboarding" }
                            ]
                        }
                    },
                    {
                        "id": "confirm_button",
                        "component_type": "button",
                        "properties": {
                            "text": "Confirm & Proceed",
                            "action": {
                                "type": "next_screen",
                                "action_id": "select-documents"
                            }
                        }
                    }
                ]
            }
        ]
    }
];
