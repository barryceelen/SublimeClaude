# SublimeClaude

A [Sublime Text](http://www.sublimetext.com) package for interacting with Anthropic's Claude API. The package is for the most part written by Claude itself.

Type "Ask Claude" in the command palette or find the "Ask Claude" menu item in the "Tools" menu or in the right-click context menu to ask a question. Any selected text in the current file will be sent along to the Claude API. Note that a Claude API key is required.

## Features

- Chat with Claude
- Send along selected code/text for context
- Configure which mode to use
- Configure a system message
- Export the current chat as a JSON file for later reference
- Import a chat JSON file to continue the discussion where you left off
- View the current chat history

## Available commands

- Ask Question
- Clear Chat History
- Show Chat History
- Export Chat History
- Import Chat History
- Switch Model
- Switch System Message

## Installation

1. In Sublime Text, add this repository via the "Package Control: Add Repository" command (use https://github.com/barryceelen/SublimeClaude)
2. Once the repository is added, use the Package Control: Install Package" command to install the `SublimeClaude` package
2. Get an API key from [Anthropic](https://console.anthropic.com/)
3. Configure API key in `Preferences > Package Settings > Sublime Claude > Settings`
