# Claudette – Claude for Sublime Text

A [Sublime Text](http://www.sublimetext.com) package for interacting with the Anthropic Claude API. The package is for the most part written by Claude AI itself.

Type "Ask Claude" in the command palette or find the "Ask Claude" item in the "Tools" menu or in the right-click context menu to ask a question. Any selected text in the current file will be sent along to the Anthropic Claude API. Note that a Claude API key is required.

## Features

- Chat with Claude
- Send along selected code/text for context
- Configure which mode to use
- Configure a system message
- Export the current chat as a JSON file for later reference
- Import a chat JSON file to continue the discussion where you left off

## Available commands
**Ask Question (claudette\_ask\_question)**  
Opens a question input prompt. Submit the prompt with the `enter` key, `shift+enter` for line breaks.

**Ask Question In New Chat View (claudette\_ask\_new\_question)**   
Opens a question input prompt. The conversation will take place in a new window. Useful for having multiple chats in the same window.

**Clear Chat History (claudette\_clear\_chat\_history)**  
Clear the chat history in the most recently active chat view in the current window. Keeps the chat history visible in the view, but new queries do not send along the previous conversation.

**Export Chat History (claudette\_export\_chat\_history)**  
Export the chat history from the most recently active chat view to a JSON file.

**Import Chat History (claudette\_export\_chat\_history)**  
Import a chat history JSON file and continue the conversation where it left off.

**Switch Model (claudette\_select\_model\_panel)**  
Switch between all available Anthropic models.

**Switch System Message (claudette\_select\_system\_message\_panel)**
Multiple system message can be added via the Claudette settings. This command allows you to switch the system message that is sent along with a conversation. 

## Key Bindings

The Claudette package does not add key bindings for its commands out of the box. The following example adds a keyboard shortcut that opens the "Ask Question" panel. You can add your own keyboard shortcuts via the Settings > Keybindings settings menu.

For OSX:

```
[
	{
		"keys": ["super+k", "super+c"],
		"command": "claudette_ask_question",
	}
]
```

For Linux and Windows:

```
[
	{
		"keys": ["ctrl+k", "ctrl+c"],
		"command": "claudette_ask_question",
	}
]
```

## Installation

1. In Sublime Text, add this repository via the "Package Control: Add Repository" command (use https://github.com/barryceelen/Claudette)
2. Once the repository is added, use the Package Control: Install Package" command to install the `Claudette` package
2. Get an API key from [Anthropic](https://console.anthropic.com/)
3. Configure API key in `Preferences > Package Settings > Claudette > Settings`
