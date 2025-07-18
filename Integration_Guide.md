# Lovable Landing Page Integration with GoHighLevel (GHL) and n8n
## Complete Step-by-Step Implementation Guide

### Project Overview
This guide provides complete instructions for integrating the Lovable landing page (https://bold-landing-pages-craft.lovable.app/) with GoHighLevel CRM and n8n automation platform for automated lead capture and management.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Step 1: Lovable Landing Page Setup](#step-1-lovable-landing-page-setup)
3. [Step 2: GoHighLevel Funnel Integration](#step-2-gohighlevel-funnel-integration)
4. [Step 3: n8n Automation Setup](#step-3-n8n-automation-setup)
5. [Step 4: Voice/IVR Integration](#step-4-voiceivr-integration)
6. [Step 5: Testing and Validation](#step-5-testing-and-validation)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Accounts and Access:
- **GoHighLevel Account**: Active subscription with API access
- **n8n Instance**: Self-hosted or cloud instance
- **Twilio Account**: For voice/IVR integration (optional)
- **Lovable Account**: Access to the landing page

### Required Information:
- GoHighLevel API Key
- GoHighLevel Location ID
- n8n Webhook URL
- Twilio Phone Number (for voice integration)

---

## Step 1: Lovable Landing Page Setup

### 1.1 Access Your Lovable Landing Page
- Navigate to: https://bold-landing-pages-craft.lovable.app/
- Log in to your Lovable account
- Access the landing page editor

### 1.2 Configure Form Integration
1. **Edit the Contact Form**:
   - Open the form editor in your Lovable page
   - Configure form fields (name, email, phone, etc.)
   - Set form action to POST to your n8n webhook

2. **Form Configuration Example**:
   ```html
   <form action="https://your-n8n-instance.com/webhook/lovable-leads" method="POST">
     <input type="text" name="name" placeholder="Full Name" required>
     <input type="email" name="email" placeholder="Email Address" required>
     <input type="tel" name="phone" placeholder="Phone Number">
     <button type="submit">Get Started</button>
   </form>
   ```

### 1.3 Test Form Submission
- Submit a test form to ensure data is being sent correctly
- Verify webhook receives the data in n8n

---

## Step 2: GoHighLevel Funnel Integration

### 2.1 Create a New Funnel in GHL
1. **Access GoHighLevel Dashboard**:
   - Log in to your GoHighLevel account
   - Navigate to Sites → Funnels
   - Click "+ New Funnel"

2. **Configure Funnel Settings**:
   - **Funnel Name**: "Lovable Landing Funnel"
   - **Domain**: Your custom domain or GHL subdomain
   - **Template**: Start with blank template

### 2.2 Add Landing Page Step
1. **Create Funnel Step**:
   - Click "+ Add Step" in your funnel
   - **Step Name**: "Lovable Landing Page"
   - **Path**: `/lovable-page`
   - **Layout**: "Blank Page"
   - Click "Create"

### 2.3 Embed Lovable Page
1. **Edit the Funnel Step**:
   - Click "Edit Page" on the newly created step
   - Drag a "Custom HTML" element into the page

2. **Add Embed Code**:
   ```html
   <iframe 
     src="https://bold-landing-pages-craft.lovable.app/" 
     width="100%" 
     height="100vh" 
     frameborder="0" 
     scrolling="no"
     style="border: none; overflow: hidden;">
   </iframe>
   ```

### 2.4 Configure iframe Settings
- **Width**: 100%
- **Height**: 100vh (full viewport height)
- **Scrolling**: Disabled (for seamless integration)
- **Border**: None

### 2.5 Save and Test
- Save the funnel step
- Preview the funnel to ensure the Lovable page loads correctly
- Test form submission from within the embedded page

---

## Step 3: n8n Automation Setup

### 3.1 Create n8n Workflow
1. **Access n8n Dashboard**:
   - Log in to your n8n instance
   - Click "New Workflow"
   - Name it "Lovable Lead Capture"

### 3.2 Set Up Webhook Node
1. **Add Webhook Node**:
   - Drag "Webhook" node to the canvas
   - Configure settings:
     - **HTTP Method**: POST
     - **Path**: `lovable-leads`
     - **Response Mode**: On Received
     - **Response Code**: 200

2. **Copy Webhook URL**:
   - Note the webhook URL: `https://your-n8n.com/webhook/lovable-leads`
   - This will be used in your Lovable form

### 3.3 Add Data Processing Node
1. **Add Set Node**:
   - Drag "Set" node after the Webhook node
   - Connect Webhook → Set

2. **Configure Data Mapping**:
   ```json
   {
     "firstName": "={{$json['name']}}",
     "email": "={{$json['email']}}",
     "phone": "={{$json['phone']}}",
     "source": "Lovable Landing Page",
     "timestamp": "={{$now}}"
   }
   ```

### 3.4 Get GoHighLevel API Credentials
1. **Access GHL API Settings**:
   - Go to GoHighLevel Dashboard
   - Navigate to Settings → Company
   - Copy your API Key

2. **Find Location ID**:
   - Go to Settings → Locations
   - Note your Location ID (usually a string of characters)

### 3.5 Configure GHL API Integration
1. **Add HTTP Request Node**:
   - Drag "HTTP Request" node after the Set node
   - Connect Set → HTTP Request

2. **Configure HTTP Request**:
   - **Method**: POST
   - **URL**: `https://rest.gohighlevel.com/v1/contacts/`
   - **Headers**:
     ```json
     {
       "Authorization": "Bearer YOUR_API_KEY",
       "Content-Type": "application/json"
     }
     ```
   - **Body (JSON)**:
     ```json
     {
       "firstName": "={{$json['firstName']}}",
       "email": "={{$json['email']}}",
       "phone": "={{$json['phone']}}",
       "locationId": "YOUR_LOCATION_ID",
       "source": "={{$json['source']}}",
       "tags": ["Lovable Lead", "Website"]
     }
     ```

### 3.6 Add Error Handling
1. **Add IF Node**:
   - Drag "IF" node after HTTP Request
   - Connect HTTP Request → IF

2. **Configure Error Logic**:
   - **Condition**: `{{$json['statusCode'] >= 400}}`
   - Add error notification or logging

### 3.7 Add Success Notification (Optional)
1. **Add HTTP Request for Success**:
   - Connect success path to notification service
   - Configure Slack, email, or other notification

### 3.8 Activate Workflow
- Save the workflow
- Click "Activate" to make it live
- Test with a form submission

---

## Step 4: Voice/IVR Integration (Optional)

### 4.1 Twilio Studio Flow Setup
1. **Access Twilio Console**:
   - Log in to Twilio Console
   - Go to Studio → Flows

2. **Create New Flow**:
   - Click "Create new Flow"
   - Import the provided flow configuration

3. **Configure Flow**:
   - Set up greeting message
   - Configure menu options (1 for sales, 2 for support)
   - Add webhook to n8n at `/webhook/voice-lead`

### 4.2 Configure Phone Number
1. **Assign Flow to Number**:
   - Go to Phone Numbers → Manage → Active numbers
   - Select your Twilio number
   - Set "A Call Comes In" to your Studio Flow

### 4.3 n8n Voice Lead Workflow
1. **Create Voice Lead Workflow**:
   - Import the voice lead workflow configuration
   - Update API credentials
   - Activate the workflow

---

## Step 5: Testing and Validation

### 5.1 Test Web Form Integration
1. **Submit Test Form**:
   - Fill out the form on your Lovable page
   - Submit and verify data appears in n8n
   - Check if contact is created in GoHighLevel

2. **Verify Data Flow**:
   - Check n8n execution logs
   - Verify contact appears in GHL contacts
   - Confirm all fields are mapped correctly

### 5.2 Test Voice Integration (if applicable)
1. **Make Test Call**:
   - Call your Twilio number
   - Follow the IVR prompts
   - Verify lead is captured in GHL

### 5.3 Monitor and Debug
1. **Check Logs**:
   - Monitor n8n execution history
   - Check GHL contact creation
   - Verify webhook responses

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: Form Not Submitting
**Symptoms**: Form submission fails, no data in n8n
**Solutions**:
- Verify webhook URL is correct
- Check if n8n workflow is activated
- Ensure form action points to correct webhook

#### Issue 2: Data Not Reaching GoHighLevel
**Symptoms**: Data in n8n but no contact in GHL
**Solutions**:
- Verify API key is correct
- Check Location ID is valid
- Ensure all required fields are mapped

#### Issue 3: iframe Not Loading
**Symptoms**: Blank page in GHL funnel
**Solutions**:
- Check iframe URL is accessible
- Verify CORS settings on Lovable page
- Test iframe in different browsers

#### Issue 4: Voice Integration Issues
**Symptoms**: Calls not being captured
**Solutions**:
- Verify Twilio Studio Flow is active
- Check webhook URL in Studio Flow
- Ensure voice workflow is activated in n8n

### Debugging Steps
1. **Check n8n Execution Logs**:
   - Go to n8n → Workflows → Execution History
   - Review failed executions for error details

2. **Verify API Credentials**:
   - Test GHL API with Postman or similar tool
   - Ensure API key has correct permissions

3. **Monitor Webhook Calls**:
   - Use webhook testing tools (webhook.site)
   - Verify data format matches expectations

---

## File Structure

```
D:\GHLSitesTest\
│
├── Integration_Guide.md           # This comprehensive guide
├── lovable-embed.html            # iframe embed code for GHL
├── lovable-form.html             # Example form configuration
├── n8n-workflow-export.json     # n8n workflow configuration
├── twilio-studio-flow.json      # Twilio Studio Flow configuration
├── api-credentials-template.json # Template for API credentials
└── README.md                     # Quick start guide
```

---

## Next Steps

### Advanced Customizations
1. **Add Lead Scoring**: Implement scoring based on form interactions
2. **Multi-Step Forms**: Create progressive form experiences
3. **A/B Testing**: Test different form variations
4. **Advanced Segmentation**: Route leads based on form data
5. **CRM Integration**: Add additional CRM integrations

### Monitoring and Analytics
1. **Set up Analytics**: Track form conversions and lead quality
2. **Performance Monitoring**: Monitor webhook response times
3. **Error Alerting**: Set up notifications for failed integrations

---

## Support and Resources

### Documentation Links
- [GoHighLevel API Documentation](https://developers.gohighlevel.com/)
- [n8n Documentation](https://docs.n8n.io/)
- [Twilio Studio Documentation](https://www.twilio.com/docs/studio)
- [Lovable Documentation](https://help.lovable.com/)

### Contact Information
- For technical support, refer to the respective platform documentation
- For custom integrations, consider hiring a developer familiar with these platforms

---

**Implementation Status**: ✅ Complete
**Last Updated**: 09-July-2025
**Version**: 1.0 