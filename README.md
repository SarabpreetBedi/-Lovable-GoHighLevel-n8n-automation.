# Lovable Landing Page Integration - Quick Start Guide

## 🚀 Quick Setup

This guide helps you integrate your Lovable landing page (https://bold-landing-pages-craft.lovable.app/) with GoHighLevel CRM and n8n automation.

## 📁 Files Included

- `Integration_Guide.md` - Complete step-by-step instructions
- `lovable-embed.html` - iframe embed code for GHL
- `lovable-form.html` - Example form configuration
- `n8n-workflow-export.json` - n8n workflow configuration
- `twilio-studio-flow.json` - Twilio voice flow
- `api-credentials-template.json` - Template for your API keys

## ⚡ Quick Steps

### 1. Configure API Credentials
1. Open `api-credentials-template.json`
2. Replace placeholder values with your actual credentials
3. Save as `api-credentials.json` (keep secure!)

### 2. Set Up n8n Workflow
1. Import `n8n-workflow-export.json` into your n8n instance
2. Update API credentials in the workflow
3. Activate the workflow

### 3. Embed in GoHighLevel
1. Create a new funnel in GHL
2. Add a blank page step
3. Use the code from `lovable-embed.html`

### 4. Update Lovable Form
1. Edit your form in Lovable
2. Set form action to your n8n webhook URL
3. Test form submission

## 🔧 Configuration Checklist

- [ ] GoHighLevel API key obtained
- [ ] n8n instance running
- [ ] Webhook URL configured
- [ ] Form action updated in Lovable
- [ ] GHL funnel created and embedded
- [ ] Test form submission
- [ ] Verify contact creation in GHL

## 📞 Voice Integration (Optional)

1. Import `twilio-studio-flow.json` into Twilio Studio
2. Configure phone number to use the flow
3. Set up voice webhook in n8n
4. Test with a phone call

## 🆘 Need Help?

1. Check the detailed `Integration_Guide.md`
2. Verify all API credentials are correct
3. Test each component individually
4. Check n8n execution logs for errors

## 📊 Testing

1. **Form Test**: Submit a test form on your Lovable page
2. **Webhook Test**: Verify data appears in n8n
3. **GHL Test**: Check if contact is created in GoHighLevel
4. **Voice Test**: Make a test call (if voice integration is set up)

## 🔒 Security Notes

- Keep API credentials secure
- Use HTTPS for all webhooks
- Regularly rotate API keys
- Monitor for unusual activity

---

**Status**: Ready for implementation
**Last Updated**: 09-July-2025
**Version**: 1.0 