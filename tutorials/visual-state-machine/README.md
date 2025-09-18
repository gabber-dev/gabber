# Visual State Machine - Phone Detector

![Visual State Machine - Phone Detector](https://readme-assets.gabber.dev/visual-state-machine-phone-detector.png)

This tutorial demonstrates how to build a conversational AI application using Gabber's visual state machine capabilities. The application tracks user payment status and phone visibility to provide context-aware responses in real-time.



## Overview

The Phone Detector app uses a state machine with two boolean parameters:
- **`paid`**: Whether the user has made a payment
- **`item_detected`**: Whether a phone is visible in the camera feed

The system dynamically updates the LLM's system prompt using Jinja templating based on the current state, enabling the conversational AI to respond appropriately to different scenarios.

## State Machine States

The application operates in four possible states:

1. **PAID_SHOWING_PHONE**: User has paid and is showing their phone
2. **PAID_NOT_SHOWING_PHONE**: User has paid but is not showing their phone  
3. **NOT_PAID_SHOWING_PHONE**: User is showing their phone but hasn't paid
4. **NOT_PAID_NOT_SHOWING_PHONE**: User hasn't paid and is not showing their phone

## How It Works

### State Detection
- **Payment Status**: Tracked through the `paid` parameter (boolean)
- **Phone Visibility**: Detected using computer vision to analyze the camera feed for phone presence

### Dynamic System Prompt
The system uses Jinja templating to dynamically update the LLM's system prompt based on the current state:

```jinja
You are a companion that is interested in what kind of phone the user has. The possible states are: PAID_SHOWING_PHONE, PAID_NOT_SHOWING_PHONE, NOT_PAID_SHOWING_PHONE, NOT_PAID_NOT_SHOWING_PHONE.

If the state has changed, I want you to respond in the following ways:

PAID_SHOWING_PHONE: The user is showing their phone. Guess what kind of phone it is. Ask how long the user has had it.

PAID_NOT_SHOWING_PHONE: The user has paid. Thank them for paying. Tell the user that you're interested in knowing what kind of phone they have and if they have one to show it.

NOT_PAID_NOT_SHOWING_PHONE: Tell the user they need to pay to get started.

NOT_PAID_SHOWING_PHONE: The user is showing their phone but they need to pay. Tell the user they need to pay before showing their phone. You are interested in what kind of phone they have.

The current state is: {{current_state}}
The previous state was: {{previous_state}}
```

### Real-time Conversation
The conversational AI can speak to users in real-time, responding contextually based on:
- Current payment status
- Whether a phone is visible
- State transitions
- User input

## Key Features

- **Visual State Machine**: Easy-to-understand state management with visual transitions
- **Dynamic Prompting**: System prompts that adapt based on application state
- **Real-time Processing**: Live audio/video processing with immediate responses
- **Computer Vision**: Automatic phone detection in camera feed
- **Context Awareness**: AI responses that understand the current situation

## Use Cases

This pattern is ideal for applications that need to:
- Track user progress through different states
- Provide context-aware responses
- Handle payment/access control scenarios
- Respond to visual cues in real-time
- Maintain conversation flow across state changes

## Getting Started

1. Import the `Visual State Machine - Phone Detector.json` file into Gabber
2. Configure your API keys for the required services
3. Run the application to see the state machine in action
4. Try different scenarios (paying, showing/hiding phone) to see how the AI responds

## Setting Up Secrets

Some nodes in this application require API keys to function properly. To configure these secrets:

1. Access the `.secret` file in your Gabber project root directory
2. Add your API keys in the following format:

```bash
# Example .secret file
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
# Add other required API keys as needed
```

3. Once your secrets are configured, they will automatically appear in dropdown menus for any node that requires them
4. The actual secret values are never stored in the graph data, ensuring safe sharing of your applications without risk of exposing your API keys

**Important**: Make sure `.secret` is added to your `.gitignore` file to prevent accidentally committing your API keys to version control. This should be configured by default.

## Technical Implementation

The state machine uses:
- **Jinja2 templating** for dynamic system prompt generation
- **Computer vision** for phone detection
- **State transitions** based on boolean parameter changes
- **Real-time audio/video processing** for conversational interaction

This demonstrates how Gabber's visual programming interface can create sophisticated, state-aware conversational AI applications with minimal code.
