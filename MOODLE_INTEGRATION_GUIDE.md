# Moodle Integration Guide

This document explains different methods for integrating the Moodle AI Learning Assistant with Moodle LMS (https://moodle.org/) websites. We'll cover several integration approaches, from full plugin development to lightweight JavaScript embedding and API-based integration.

## Table of Contents

1. [Integration Options Overview](#integration-options-overview)
2. [PHP Plugin Development](#php-plugin-development)
3. [JavaScript Widget Integration](#javascript-widget-integration)
4. [LTI (Learning Tools Interoperability) Integration](#lti-learning-tools-interoperability-integration)
5. [REST API Integration](#rest-api-integration)
6. [WebHook-Based Integration](#webhook-based-integration)
7. [Single Sign-On (SSO) Configuration](#single-sign-on-sso-configuration)
8. [Data Synchronization Strategies](#data-synchronization-strategies)
9. [Troubleshooting Common Issues](#troubleshooting-common-issues)

## Integration Options Overview

There are several ways to integrate the Moodle AI Learning Assistant with Moodle:

| Integration Method | Complexity | Depth of Integration | Use Case |
|-------------------|------------|----------------------|----------|
| PHP Plugin | High | Deep | Full integration with Moodle's core functions |
| JavaScript Widget | Low | Shallow | Quick integration without server modifications |
| LTI Integration | Medium | Medium | Standard-based integration with minimal customization |
| REST API | Medium | Customizable | Flexible data exchange between systems |
| WebHook-Based | Medium | Event-driven | Real-time updates on specific actions |

Choose the integration method that best fits your technical expertise, access level to the Moodle installation, and specific requirements.

## PHP Plugin Development

Creating a native Moodle plugin provides the deepest integration and access to all Moodle features. This approach requires PHP development skills and access to the Moodle file system.

### Plugin Types

Moodle supports several plugin types, each with different capabilities and integration points:

1. **Block Plugin**: Adds a block to Moodle pages with the AI Assistant interface
2. **Local Plugin**: Provides background functionality without a specific integration point
3. **Activity Module**: Creates a new activity type for AI-assisted learning

For the AI Learning Assistant, a **Block Plugin** combined with a **Local Plugin** typically works best.

### Step-by-Step Plugin Development

#### 1. Set Up Development Environment

```bash
# Clone Moodle repository or access your existing installation
git clone https://github.com/moodle/moodle.git
cd moodle

# Create plugin directories
mkdir -p blocks/ai_assistant
mkdir -p local/ai_assistant_core
```

#### 2. Create Block Plugin Structure

Create the following files for the block plugin:

**blocks/ai_assistant/block_ai_assistant.php**:
```php
<?php
defined('MOODLE_INTERNAL') || die();

class block_ai_assistant extends block_base {
    public function init() {
        $this->title = get_string('pluginname', 'block_ai_assistant');
    }

    public function get_content() {
        if ($this->content !== null) {
            return $this->content;
        }

        $this->content = new stdClass;
        $this->content->text = $this->render_assistant_interface();
        $this->content->footer = '';

        return $this->content;
    }

    protected function render_assistant_interface() {
        global $CFG, $COURSE;

        // Load configuration
        $config = get_config('block_ai_assistant');
        $apiurl = !empty($config->apiurl) ? $config->apiurl : 'http://localhost:5000/api';

        // Create container with unique ID
        $html = '<div id="ai-assistant-container" class="ai-assistant-block" 
                     data-course-id="' . $COURSE->id . '" 
                     data-api-url="' . $apiurl . '">';
        
        $html .= '<div class="ai-assistant-header">' . get_string('chat_with_assistant', 'block_ai_assistant') . '</div>';
        $html .= '<div id="ai-assistant-messages" class="ai-assistant-messages"></div>';
        $html .= '<div class="ai-assistant-input">';
        $html .= '<input type="text" id="ai-assistant-query" placeholder="' . get_string('ask_question', 'block_ai_assistant') . '">';
        $html .= '<button id="ai-assistant-send">' . get_string('send', 'block_ai_assistant') . '</button>';
        $html .= '</div>';
        
        $html .= '</div>';

        // Add JavaScript for functionality
        $html .= '<script src="' . new moodle_url('/blocks/ai_assistant/js/assistant.js') . '"></script>';
        
        return $html;
    }

    public function applicable_formats() {
        return [
            'all' => true,
            'site' => true,
            'site-index' => true,
            'course-view' => true,
            'mod' => true,
        ];
    }

    public function has_config() {
        return true;
    }
}
```

**blocks/ai_assistant/version.php**:
```php
<?php
defined('MOODLE_INTERNAL') || die();

$plugin->component = 'block_ai_assistant';
$plugin->version = 2025040300;
$plugin->requires = 2022041900; // Moodle 4.0
$plugin->maturity = MATURITY_BETA;
$plugin->release = '0.1.0';
$plugin->dependencies = [
    'local_ai_assistant_core' => 2025040300
];
```

**blocks/ai_assistant/lang/en/block_ai_assistant.php**:
```php
<?php
$string['pluginname'] = 'AI Learning Assistant';
$string['chat_with_assistant'] = 'Chat with AI Learning Assistant';
$string['ask_question'] = 'Ask a question...';
$string['send'] = 'Send';
$string['loading'] = 'Thinking...';
$string['config_apiurl'] = 'AI Assistant API URL';
$string['config_apiurl_desc'] = 'The URL of the AI Assistant API (e.g., http://your-server:5000/api)';
$string['config_apikey'] = 'API Key';
$string['config_apikey_desc'] = 'API key for authenticating with the AI Assistant service';
```

**blocks/ai_assistant/settings.php**:
```php
<?php
defined('MOODLE_INTERNAL') || die;

if ($ADMIN->fulltree) {
    $settings->add(new admin_setting_configtext(
        'block_ai_assistant/apiurl',
        get_string('config_apiurl', 'block_ai_assistant'),
        get_string('config_apiurl_desc', 'block_ai_assistant'),
        'http://localhost:5000/api',
        PARAM_URL
    ));
    
    $settings->add(new admin_setting_configpasswordunmask(
        'block_ai_assistant/apikey',
        get_string('config_apikey', 'block_ai_assistant'),
        get_string('config_apikey_desc', 'block_ai_assistant'),
        '',
        PARAM_TEXT
    ));
}
```

**blocks/ai_assistant/js/assistant.js**:
```javascript
document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('ai-assistant-container');
    if (!container) return;
    
    const messagesContainer = document.getElementById('ai-assistant-messages');
    const queryInput = document.getElementById('ai-assistant-query');
    const sendButton = document.getElementById('ai-assistant-send');
    
    const courseId = container.dataset.courseId;
    const apiUrl = container.dataset.apiUrl;
    
    // Function to add message to the chat
    function addMessage(text, isUser) {
        const messageDiv = document.createElement('div');
        messageDiv.className = isUser ? 'ai-assistant-user-message' : 'ai-assistant-ai-message';
        messageDiv.textContent = text;
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    // Function to send message to API
    async function sendMessage(message) {
        try {
            const loadingMsg = document.createElement('div');
            loadingMsg.className = 'ai-assistant-ai-message ai-assistant-loading';
            loadingMsg.textContent = M.util.get_string('loading', 'block_ai_assistant');
            messagesContainer.appendChild(loadingMsg);
            
            const response = await fetch(`${apiUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + M.cfg.sesskey // Use Moodle session key for auth
                },
                body: JSON.stringify({
                    message: message,
                    course_id: courseId
                })
            });
            
            const data = await response.json();
            
            // Remove loading message
            messagesContainer.removeChild(loadingMsg);
            
            // Add response
            if (data.response) {
                addMessage(data.response, false);
            } else if (data.error) {
                addMessage('Error: ' + data.error, false);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            messagesContainer.removeChild(document.querySelector('.ai-assistant-loading'));
            addMessage('Sorry, something went wrong. Please try again later.', false);
        }
    }
    
    // Handle send button click
    sendButton.addEventListener('click', function() {
        const message = queryInput.value.trim();
        if (message) {
            addMessage(message, true);
            queryInput.value = '';
            sendMessage(message);
        }
    });
    
    // Handle enter key press
    queryInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendButton.click();
        }
    });
});
```

**blocks/ai_assistant/styles.css**:
```css
.ai-assistant-block {
    display: flex;
    flex-direction: column;
    height: 400px;
    border: 1px solid #ddd;
    border-radius: 8px;
    overflow: hidden;
}

.ai-assistant-header {
    background-color: #0f6cbf;
    color: white;
    padding: 10px;
    font-weight: bold;
}

.ai-assistant-messages {
    flex-grow: 1;
    padding: 10px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.ai-assistant-user-message,
.ai-assistant-ai-message {
    max-width: 80%;
    padding: 8px 12px;
    border-radius: 18px;
    word-break: break-word;
}

.ai-assistant-user-message {
    align-self: flex-end;
    background-color: #dcf8c6;
}

.ai-assistant-ai-message {
    align-self: flex-start;
    background-color: #f1f0f0;
}

.ai-assistant-loading {
    font-style: italic;
    opacity: 0.7;
}

.ai-assistant-input {
    display: flex;
    padding: 10px;
    border-top: 1px solid #ddd;
}

.ai-assistant-input input {
    flex-grow: 1;
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 20px;
    margin-right: 8px;
}

.ai-assistant-input button {
    background-color: #0f6cbf;
    color: white;
    border: none;
    border-radius: 20px;
    padding: 8px 16px;
    cursor: pointer;
}
```

#### 3. Create Local Plugin for Core Functionality

**local/ai_assistant_core/version.php**:
```php
<?php
defined('MOODLE_INTERNAL') || die();

$plugin->component = 'local_ai_assistant_core';
$plugin->version = 2025040300;
$plugin->requires = 2022041900; // Moodle 4.0
$plugin->maturity = MATURITY_BETA;
$plugin->release = '0.1.0';
```

**local/ai_assistant_core/lib.php**:
```php
<?php
defined('MOODLE_INTERNAL') || die();

/**
 * Make API request to AI Assistant service
 * 
 * @param string $endpoint The API endpoint
 * @param array $data The data to send
 * @return object Response from API
 */
function local_ai_assistant_core_api_request($endpoint, $data = []) {
    $config = get_config('block_ai_assistant');
    $apiurl = !empty($config->apiurl) ? rtrim($config->apiurl, '/') : 'http://localhost:5000/api';
    $apikey = !empty($config->apikey) ? $config->apikey : '';
    
    $url = $apiurl . '/' . ltrim($endpoint, '/');
    
    $curl = new curl();
    $curl->setHeader(['Content-Type: application/json']);
    
    if (!empty($apikey)) {
        $curl->setHeader(['Authorization: Bearer ' . $apikey]);
    }
    
    $response = $curl->post($url, json_encode($data));
    $result = json_decode($response);
    
    if (!$result) {
        return (object) [
            'success' => false,
            'error' => 'Invalid response from API'
        ];
    }
    
    return $result;
}

/**
 * Get course content for the AI Assistant
 * 
 * @param int $courseid The course ID
 * @return array Course content
 */
function local_ai_assistant_core_get_course_content($courseid) {
    global $DB;
    
    $course = $DB->get_record('course', ['id' => $courseid], '*', MUST_EXIST);
    $coursecontext = context_course::instance($course->id);
    
    $content = [];
    
    // Get course sections and content
    $modinfo = get_fast_modinfo($course);
    
    foreach ($modinfo->get_section_info_all() as $section) {
        if (!empty($modinfo->sections[$section->section])) {
            foreach ($modinfo->sections[$section->section] as $cmid) {
                $cm = $modinfo->cms[$cmid];
                
                if (!$cm->uservisible) {
                    continue;
                }
                
                // Get module details
                $module = [
                    'id' => $cm->id,
                    'name' => $cm->name,
                    'type' => $cm->modname,
                    'section' => $section->section,
                    'content' => '',
                    'url' => $cm->url ? $cm->url->out() : '',
                ];
                
                // For certain module types, try to get the content
                if ($cm->modname == 'page') {
                    $page = $DB->get_record('page', ['id' => $cm->instance], '*', IGNORE_MISSING);
                    if ($page) {
                        $module['content'] = $page->content;
                    }
                } else if ($cm->modname == 'book') {
                    $book = $DB->get_record('book', ['id' => $cm->instance], '*', IGNORE_MISSING);
                    if ($book) {
                        $chapters = $DB->get_records('book_chapters', ['bookid' => $book->id], 'pagenum');
                        foreach ($chapters as $chapter) {
                            $module['content'] .= $chapter->title . "\n\n" . $chapter->content . "\n\n";
                        }
                    }
                }
                
                $content[] = $module;
            }
        }
    }
    
    return [
        'course' => [
            'id' => $course->id,
            'fullname' => $course->fullname,
            'shortname' => $course->shortname,
            'summary' => $course->summary,
        ],
        'modules' => $content
    ];
}

/**
 * Sync course content with AI Assistant service
 * 
 * @param int $courseid The course ID
 * @return object Response from API
 */
function local_ai_assistant_core_sync_course($courseid) {
    $content = local_ai_assistant_core_get_course_content($courseid);
    return local_ai_assistant_core_api_request('sync-course', $content);
}
```

**local/ai_assistant_core/lang/en/local_ai_assistant_core.php**:
```php
<?php
$string['pluginname'] = 'AI Learning Assistant Core';
```

#### 4. Installing the Plugins in Moodle

1. Compress each plugin folder (`blocks/ai_assistant` and `local/ai_assistant_core`) as separate ZIP files
2. Go to Site Administration > Plugins > Install Plugins
3. Upload and install each ZIP file
4. Follow the installation prompts
5. Configure the block plugin settings with your AI Assistant API URL and key

### Extending the Plugin with Advanced Features

You can extend the basic plugin with more features:

#### Course Content Sync

**local/ai_assistant_core/classes/task/sync_course_content.php**:
```php
<?php
namespace local_ai_assistant_core\task;

defined('MOODLE_INTERNAL') || die();

class sync_course_content extends \core\task\scheduled_task {
    public function get_name() {
        return get_string('sync_course_content', 'local_ai_assistant_core');
    }

    public function execute() {
        global $DB;
        
        mtrace('Starting AI Assistant course content sync');
        
        $courses = $DB->get_records('course', ['visible' => 1]);
        
        foreach ($courses as $course) {
            mtrace('Syncing course: ' . $course->fullname);
            
            try {
                $result = local_ai_assistant_core_sync_course($course->id);
                
                if (isset($result->success) && $result->success) {
                    mtrace('Successfully synced course ID ' . $course->id);
                } else {
                    mtrace('Failed to sync course ID ' . $course->id . ': ' . 
                           (isset($result->error) ? $result->error : 'Unknown error'));
                }
            } catch (\Exception $e) {
                mtrace('Exception when syncing course ID ' . $course->id . ': ' . $e->getMessage());
            }
        }
        
        mtrace('AI Assistant course content sync completed');
    }
}
```

**local/ai_assistant_core/db/tasks.php**:
```php
<?php
defined('MOODLE_INTERNAL') || die();

$tasks = [
    [
        'classname' => 'local_ai_assistant_core\task\sync_course_content',
        'blocking' => 0,
        'minute' => '0',
        'hour' => '*/6',
        'day' => '*',
        'month' => '*',
        'dayofweek' => '*',
    ],
];
```

## JavaScript Widget Integration

For a simpler integration that doesn't require PHP plugin development, you can use a JavaScript widget that can be embedded anywhere in your Moodle site.

### Step 1: Create the Widget Script

Create a JavaScript file (`ai-assistant-widget.js`) that can be hosted on your AI Assistant server or a CDN:

```javascript
(function() {
    // Configuration
    const config = {
        apiUrl: 'https://your-ai-assistant-server.com/api',
        apiKey: '', // Set this securely
        position: 'bottom-right', // Widget position
        width: '350px',
        height: '500px',
    };
    
    // Create widget container
    const createWidget = () => {
        const container = document.createElement('div');
        container.id = 'ai-assistant-widget-container';
        container.style.position = 'fixed';
        
        // Set position
        if (config.position === 'bottom-right') {
            container.style.bottom = '20px';
            container.style.right = '20px';
        } else if (config.position === 'bottom-left') {
            container.style.bottom = '20px';
            container.style.left = '20px';
        }
        
        container.style.width = config.width;
        container.style.height = config.height;
        container.style.zIndex = '9999';
        container.style.display = 'flex';
        container.style.flexDirection = 'column';
        container.style.boxShadow = '0 5px 40px rgba(0, 0, 0, 0.16)';
        container.style.borderRadius = '8px';
        container.style.background = '#fff';
        container.style.overflow = 'hidden';
        
        // Create header
        const header = document.createElement('div');
        header.style.padding = '12px 15px';
        header.style.background = '#0f6cbf';
        header.style.color = '#fff';
        header.style.fontWeight = 'bold';
        header.style.display = 'flex';
        header.style.justifyContent = 'space-between';
        header.style.alignItems = 'center';
        header.textContent = 'AI Learning Assistant';
        
        // Create minimize button
        const minimizeBtn = document.createElement('button');
        minimizeBtn.textContent = '−';
        minimizeBtn.style.background = 'none';
        minimizeBtn.style.border = 'none';
        minimizeBtn.style.color = '#fff';
        minimizeBtn.style.fontSize = '20px';
        minimizeBtn.style.cursor = 'pointer';
        header.appendChild(minimizeBtn);
        
        // Create content area
        const content = document.createElement('div');
        content.style.flex = '1';
        content.style.display = 'flex';
        content.style.flexDirection = 'column';
        
        // Create messages area
        const messages = document.createElement('div');
        messages.style.flex = '1';
        messages.style.padding = '15px';
        messages.style.overflowY = 'auto';
        messages.style.display = 'flex';
        messages.style.flexDirection = 'column';
        messages.style.gap = '10px';
        content.appendChild(messages);
        
        // Create input area
        const inputArea = document.createElement('div');
        inputArea.style.borderTop = '1px solid #eee';
        inputArea.style.padding = '10px';
        inputArea.style.display = 'flex';
        content.appendChild(inputArea);
        
        // Create text input
        const input = document.createElement('input');
        input.type = 'text';
        input.placeholder = 'Ask a question...';
        input.style.flex = '1';
        input.style.padding = '8px 12px';
        input.style.border = '1px solid #ddd';
        input.style.borderRadius = '20px';
        input.style.marginRight = '8px';
        inputArea.appendChild(input);
        
        // Create send button
        const sendBtn = document.createElement('button');
        sendBtn.textContent = 'Send';
        sendBtn.style.background = '#0f6cbf';
        sendBtn.style.color = '#fff';
        sendBtn.style.border = 'none';
        sendBtn.style.borderRadius = '20px';
        sendBtn.style.padding = '8px 16px';
        sendBtn.style.cursor = 'pointer';
        inputArea.appendChild(sendBtn);
        
        // Add elements to container
        container.appendChild(header);
        container.appendChild(content);
        
        // Create collapsed button (initially hidden)
        const collapsedBtn = document.createElement('div');
        collapsedBtn.id = 'ai-assistant-widget-collapsed';
        collapsedBtn.style.position = 'fixed';
        collapsedBtn.style.bottom = '20px';
        collapsedBtn.style.right = '20px';
        collapsedBtn.style.width = '60px';
        collapsedBtn.style.height = '60px';
        collapsedBtn.style.borderRadius = '50%';
        collapsedBtn.style.background = '#0f6cbf';
        collapsedBtn.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.15)';
        collapsedBtn.style.cursor = 'pointer';
        collapsedBtn.style.display = 'none';
        collapsedBtn.style.justifyContent = 'center';
        collapsedBtn.style.alignItems = 'center';
        collapsedBtn.style.zIndex = '9999';
        collapsedBtn.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M20 2H4C2.9 2 2 2.9 2 4V22L6 18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2Z" fill="white"/></svg>';
        
        // Add to document
        document.body.appendChild(container);
        document.body.appendChild(collapsedBtn);
        
        // Event listeners for minimizing/expanding
        minimizeBtn.addEventListener('click', () => {
            container.style.display = 'none';
            collapsedBtn.style.display = 'flex';
        });
        
        collapsedBtn.addEventListener('click', () => {
            container.style.display = 'flex';
            collapsedBtn.style.display = 'none';
        });
        
        // Function to add message
        const addMessage = (text, isUser) => {
            const message = document.createElement('div');
            message.style.maxWidth = '80%';
            message.style.padding = '8px 12px';
            message.style.borderRadius = '18px';
            message.style.wordBreak = 'break-word';
            
            if (isUser) {
                message.style.alignSelf = 'flex-end';
                message.style.background = '#dcf8c6';
            } else {
                message.style.alignSelf = 'flex-start';
                message.style.background = '#f1f0f0';
            }
            
            message.textContent = text;
            messages.appendChild(message);
            messages.scrollTop = messages.scrollHeight;
        };
        
        // Function to send message
        const sendMessage = async (text) => {
            try {
                const courseId = getMoodleCourseId();
                
                const loadingMsg = document.createElement('div');
                loadingMsg.style.alignSelf = 'flex-start';
                loadingMsg.style.background = '#f1f0f0';
                loadingMsg.style.padding = '8px 12px';
                loadingMsg.style.borderRadius = '18px';
                loadingMsg.style.fontStyle = 'italic';
                loadingMsg.style.opacity = '0.7';
                loadingMsg.textContent = 'Thinking...';
                messages.appendChild(loadingMsg);
                
                const response = await fetch(`${config.apiUrl}/chat`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': config.apiKey ? `Bearer ${config.apiKey}` : undefined
                    },
                    body: JSON.stringify({
                        message: text,
                        course_id: courseId
                    })
                });
                
                const data = await response.json();
                
                // Remove loading message
                messages.removeChild(loadingMsg);
                
                // Add response
                if (data.response) {
                    addMessage(data.response, false);
                } else if (data.error) {
                    addMessage('Error: ' + data.error, false);
                }
            } catch (error) {
                console.error('Error sending message:', error);
                messages.removeChild(messages.querySelector('[style*="font-style: italic"]'));
                addMessage('Sorry, something went wrong. Please try again later.', false);
            }
        };
        
        // Handle send button click
        sendBtn.addEventListener('click', () => {
            const message = input.value.trim();
            if (message) {
                addMessage(message, true);
                input.value = '';
                sendMessage(message);
            }
        });
        
        // Handle enter key press
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendBtn.click();
            }
        });
        
        // Welcome message
        addMessage('Hello! I'm your AI Learning Assistant. How can I help you today?', false);
    };
    
    // Try to detect Moodle course ID
    const getMoodleCourseId = () => {
        try {
            // Method 1: From URL
            const match = location.pathname.match(/\/course\/view\.php\?id=(\d+)/);
            if (match && match[1]) {
                return parseInt(match[1], 10);
            }
            
            // Method 2: From body class
            const bodyClasses = document.body.className.split(' ');
            for (const cls of bodyClasses) {
                if (cls.startsWith('course-')) {
                    const courseId = cls.replace('course-', '');
                    if (/^\d+$/.test(courseId)) {
                        return parseInt(courseId, 10);
                    }
                }
            }
            
            // Method 3: From page context
            if (typeof M !== 'undefined' && M.cfg && M.cfg.contextid) {
                return M.cfg.contextid;
            }
        } catch (error) {
            console.error('Error getting course ID:', error);
        }
        
        return null;
    };
    
    // Initialize widget when DOM is loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', createWidget);
    } else {
        createWidget();
    }
})();
```

### Step 2: Add the Widget to Moodle

There are multiple ways to add the JavaScript widget to Moodle:

#### Option 1: Add to Theme

1. Navigate to Site Administration > Appearance > Themes > Theme Settings
2. In the "Raw SCSS" or "Additional HTML" section, add:

```html
<script src="https://your-cdn-or-server.com/ai-assistant-widget.js"></script>
```

#### Option 2: Use Custom HTML Block

1. Turn editing on in a Moodle course
2. Add a "HTML" block
3. Edit the block and add:

```html
<script src="https://your-cdn-or-server.com/ai-assistant-widget.js"></script>
```

#### Option 3: Add to Footer

1. Navigate to Site Administration > Appearance > Additional HTML
2. In the "Before BODY is closed" section, add:

```html
<script src="https://your-cdn-or-server.com/ai-assistant-widget.js"></script>
```

### Step 3: Configure Widget Security

To prevent unauthorized access to your AI Assistant API:

1. Use CORS headers on your API to restrict domains that can make requests
2. Implement proper authentication on your API endpoints (JWT tokens, API keys)
3. Consider using server-side proxying in Moodle to make the actual API requests

## LTI (Learning Tools Interoperability) Integration

LTI is a standard protocol for integrating external tools with learning management systems. This approach provides a secure, standardized way to integrate without custom development.

### Step 1: Set Up Your AI Assistant as an LTI Provider

1. Create an LTI provider endpoint in your AI Assistant application.

Add the following code to your FastAPI application:

**fastapi_app/routers/lti.py**:
```python
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import hashlib
import base64
import time
import os

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# LTI configuration
LTI_CONSUMER_KEY = os.getenv("LTI_CONSUMER_KEY", "moodle")
LTI_SHARED_SECRET = os.getenv("LTI_SHARED_SECRET", "secret")

@router.post("/lti", response_class=HTMLResponse)
async def lti_launch(
    request: Request,
    oauth_consumer_key: str = Form(...),
    oauth_signature: str = Form(...),
    oauth_timestamp: str = Form(...),
    oauth_nonce: str = Form(...),
    oauth_signature_method: str = Form(...),
    user_id: str = Form(...),
    context_id: str = Form(..., alias="custom_course_id"),
    roles: str = Form(...),
    lis_person_name_full: str = Form(None),
    resource_link_id: str = Form(...),
):
    # Validate LTI request
    if oauth_consumer_key != LTI_CONSUMER_KEY:
        raise HTTPException(status_code=401, detail="Invalid consumer key")
    
    # In production, implement complete OAuth validation
    # For simplicity, we're skipping signature validation here
    
    # Determine user role
    is_instructor = any(role in roles for role in ["Instructor", "Faculty", "Teacher"])
    
    # Store user session information
    # In production, implement proper session management
    
    # Render the appropriate interface
    return templates.TemplateResponse(
        "lti_launch.html", 
        {
            "request": request,
            "user_id": user_id,
            "course_id": context_id,
            "user_name": lis_person_name_full,
            "is_instructor": is_instructor
        }
    )
```

**templates/lti_launch.html**:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Learning Assistant</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <style>
        .chat-container {
            height: 500px;
            display: flex;
            flex-direction: column;
        }
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 15px;
            background-color: #f8f9fa;
        }
        .message {
            margin-bottom: 15px;
            padding: 10px;
            border-radius: 10px;
            max-width: 80%;
        }
        .user-message {
            background-color: #dcf8c6;
            align-self: flex-end;
            margin-left: auto;
        }
        .ai-message {
            background-color: #f1f0f0;
        }
        .input-area {
            padding: 15px;
            border-top: 1px solid #ddd;
        }
    </style>
</head>
<body>
    <div class="container py-4">
        <h2>AI Learning Assistant</h2>
        <p>Welcome, {{ user_name }}</p>
        
        <div class="chat-container">
            <div class="messages" id="messages"></div>
            
            <div class="input-area">
                <div class="input-group">
                    <input type="text" id="message-input" class="form-control" placeholder="Ask a question...">
                    <button class="btn btn-primary" id="send-button">Send</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Store context information
        const userData = {
            userId: "{{ user_id }}",
            courseId: "{{ course_id }}",
            isInstructor: {{ 'true' if is_instructor else 'false' }}
        };
        
        document.addEventListener('DOMContentLoaded', function() {
            const messagesContainer = document.getElementById('messages');
            const messageInput = document.getElementById('message-input');
            const sendButton = document.getElementById('send-button');
            
            // Add welcome message
            addMessage('Hello! I'm your AI Learning Assistant. How can I help you with this course?', false);
            
            // Add event listeners
            sendButton.addEventListener('click', sendMessage);
            messageInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
            
            function addMessage(text, isUser) {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${isUser ? 'user-message' : 'ai-message'}`;
                messageDiv.textContent = text;
                messagesContainer.appendChild(messageDiv);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
            
            function sendMessage() {
                const message = messageInput.value.trim();
                if (!message) return;
                
                addMessage(message, true);
                messageInput.value = '';
                
                // Add loading indicator
                const loadingDiv = document.createElement('div');
                loadingDiv.className = 'message ai-message';
                loadingDiv.textContent = 'Thinking...';
                loadingDiv.style.opacity = '0.7';
                loadingDiv.style.fontStyle = 'italic';
                messagesContainer.appendChild(loadingDiv);
                
                // Send to API
                fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        message: message,
                        course_id: userData.courseId,
                        user_id: userData.userId
                    })
                })
                .then(response => response.json())
                .then(data => {
                    // Remove loading indicator
                    messagesContainer.removeChild(loadingDiv);
                    
                    // Add response
                    if (data.response) {
                        addMessage(data.response, false);
                    } else if (data.error) {
                        addMessage('Error: ' + data.error, false);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    messagesContainer.removeChild(loadingDiv);
                    addMessage('Sorry, something went wrong. Please try again later.', false);
                });
            }
        });
    </script>
</body>
</html>
```

### Step 2: Configure Moodle as an LTI Consumer

1. Log in to Moodle as an administrator
2. Go to Site Administration > Plugins > External tools > Manage tools
3. Click "Configure a tool manually"
4. Fill in the tool configuration:
   - Tool name: "AI Learning Assistant"
   - Tool URL: `https://your-ai-assistant-server.com/api/lti`
   - Consumer key: The same value as `LTI_CONSUMER_KEY` in your code
   - Shared secret: The same value as `LTI_SHARED_SECRET` in your code
   - Default launch container: Embed without blocks
5. Configure any other desired options (privacy, custom parameters, etc.)
6. Save the tool configuration

### Step 3: Add the LTI Tool to a Course

1. Go to a course where you want to add the AI Assistant
2. Turn editing on
3. Click "Add an activity or resource"
4. Select "External tool"
5. Configure the activity:
   - Activity name: "AI Learning Assistant"
   - Preconfigured tool: Select the tool you configured earlier
   - Custom parameters: Add any additional parameters you want to pass
6. Save and display the activity

The AI Learning Assistant will now appear as an embedded tool within your Moodle course.

## REST API Integration

Instead of embedding the AI Assistant directly in Moodle, you can use Moodle's REST API to sync data with your AI Assistant service.

### Step 1: Set Up Moodle Web Services

1. Enable Web Services in Moodle:
   - Site Administration > Advanced features > Enable web services
   - Site Administration > Plugins > Web services > Enable protocols > Enable REST protocol
   
2. Create a custom service:
   - Site Administration > Plugins > Web services > External services
   - Add a new service named "AI Assistant Integration"
   - Enable "Authorized users only"
   - Add the following functions to the service:
     - `core_course_get_courses`
     - `core_course_get_contents`
     - `core_user_get_users`
     - `core_course_get_user_administration_options`
     - `core_course_get_user_enrolments`
     
3. Create a service user:
   - Create a new user with appropriate permissions
   - Add this user as an authorized user for your service
   
4. Create a token for the user:
   - Site Administration > Plugins > Web services > Manage tokens
   - Create a token for your service user

### Step 2: Create a Moodle API Client in Your AI Assistant

Create a Moodle API client module in your AI Assistant application:

**services/moodle_api_client.py**:
```python
import os
import requests
from urllib.parse import urljoin
import logging

class MoodleAPIClient:
    def __init__(self):
        self.base_url = os.environ.get("MOODLE_URL", "https://your-moodle-site.com")
        self.token = os.environ.get("MOODLE_TOKEN")
        self.logger = logging.getLogger(__name__)
        
        if not self.token:
            self.logger.warning("MOODLE_TOKEN environment variable not set")
    
    def call_api(self, function, params=None):
        """Call the Moodle API with the given function and parameters"""
        if not self.token:
            return {"error": "MOODLE_TOKEN not configured"}
            
        url = urljoin(self.base_url, "/webservice/rest/server.php")
        
        data = {
            "wstoken": self.token,
            "wsfunction": function,
            "moodlewsrestformat": "json"
        }
        
        if params:
            data.update(params)
            
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            
            result = response.json()
            
            # Check for Moodle API errors
            if isinstance(result, dict) and "exception" in result:
                self.logger.error(f"Moodle API error: {result}")
                return {"error": result.get("message", "Unknown Moodle API error")}
                
            return result
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error calling Moodle API: {e}")
            return {"error": str(e)}
    
    def get_courses(self):
        """Get all courses"""
        return self.call_api("core_course_get_courses")
    
    def get_course_content(self, course_id):
        """Get course content"""
        return self.call_api("core_course_get_contents", {"courseid": course_id})
    
    def get_course_users(self, course_id):
        """Get users enrolled in a course"""
        # First get the course's context ID
        course_data = self.call_api("core_course_get_courses", {"ids": [course_id]})
        
        if "error" in course_data:
            return course_data
            
        if not course_data or not isinstance(course_data, list) or len(course_data) == 0:
            return {"error": "Course not found"}
            
        # Now get the enrolled users
        result = self.call_api("core_enrol_get_enrolled_users", {"courseid": course_id})
        return result
    
    def sync_course_to_ai_assistant(self, course_id):
        """Sync a course to the AI Assistant database"""
        # Get course data
        course_data = self.call_api("core_course_get_courses", {"ids": [course_id]})
        
        if "error" in course_data:
            return course_data
            
        if not course_data or not isinstance(course_data, list) or len(course_data) == 0:
            return {"error": "Course not found"}
            
        # Get course content
        content_data = self.call_api("core_course_get_contents", {"courseid": course_id})
        
        if "error" in content_data:
            return content_data
        
        # Process and store course data in the AI Assistant database
        # This would call your AI Assistant's database functions
        
        course_info = course_data[0]
        processed_content = self._process_course_content(content_data)
        
        # Here you would store this data in your database
        # For example: store_course_in_db(course_info, processed_content)
        
        return {
            "success": True,
            "course": {
                "id": course_info.get("id"),
                "name": course_info.get("fullname"),
                "content_items": len(processed_content)
            }
        }
    
    def _process_course_content(self, content_data):
        """Process and extract relevant content from Moodle course data"""
        processed_items = []
        
        for section in content_data:
            section_name = section.get("name")
            
            for module in section.get("modules", []):
                module_name = module.get("name")
                module_type = module.get("modname")
                module_id = module.get("id")
                
                content_text = ""
                
                # Extract content based on module type
                if module_type == "page" and "contents" in module:
                    content_text = module["contents"]
                elif module_type == "resource" and "contents" in module:
                    content_text = module["contents"]
                elif module_type == "url" and "contents" in module:
                    content_text = f"URL: {module.get('contents', '')}"
                
                processed_items.append({
                    "section": section_name,
                    "title": module_name,
                    "type": module_type,
                    "content": content_text,
                    "module_id": module_id
                })
        
        return processed_items
```

### Step 3: Create API Endpoint for Course Sync

Add a route to trigger course synchronization:

**routes/moodle_api.py**:
```python
from flask import Blueprint, request, jsonify
from services.moodle_api_client import MoodleAPIClient
from app import db
from models import Course, CourseContent
import logging

moodle_api_bp = Blueprint('moodle_api', __name__)
logger = logging.getLogger(__name__)

@moodle_api_bp.route('/api/moodle/sync-course', methods=['POST'])
def sync_course():
    """Sync a Moodle course to the local database"""
    
    data = request.json
    course_id = data.get('course_id')
    
    if not course_id:
        return jsonify({"error": "course_id is required"}), 400
    
    client = MoodleAPIClient()
    
    # Get course data from Moodle
    course_data = client.call_api("core_course_get_courses", {"ids": [course_id]})
    
    if "error" in course_data:
        logger.error(f"Error retrieving course data: {course_data['error']}")
        return jsonify({"error": course_data["error"]}), 500
        
    if not course_data or not isinstance(course_data, list) or len(course_data) == 0:
        return jsonify({"error": "Course not found"}), 404
    
    # Get course content
    content_data = client.call_api("core_course_get_contents", {"courseid": course_id})
    
    if "error" in content_data:
        logger.error(f"Error retrieving course content: {content_data['error']}")
        return jsonify({"error": content_data["error"]}), 500
    
    # Process course data
    try:
        course_info = course_data[0]
        
        # Create or update course record
        course = Course.query.filter_by(moodle_course_id=course_info["id"]).first()
        
        if not course:
            course = Course(
                moodle_course_id=course_info["id"],
                title=course_info["fullname"],
                description=course_info.get("summary", "")
            )
            db.session.add(course)
            db.session.commit()
        else:
            course.title = course_info["fullname"]
            course.description = course_info.get("summary", "")
            db.session.commit()
        
        # Process content
        content_count = process_course_content(course.id, content_data)
        
        return jsonify({
            "success": True,
            "course": {
                "id": course.id,
                "moodle_id": course.moodle_course_id,
                "title": course.title,
                "content_items": content_count
            }
        })
    
    except Exception as e:
        logger.exception(f"Error processing course data: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

def process_course_content(course_id, content_data):
    """Process and store course content"""
    content_count = 0
    
    for section in content_data:
        section_name = section.get("name")
        
        for module in section.get("modules", []):
            if not module.get("name"):
                continue
                
            module_name = module.get("name")
            module_type = module.get("modname")
            module_id = module.get("id")
            
            content_text = ""
            url = ""
            
            # Extract content based on module type
            if module_type == "page" and "contents" in module:
                content_text = module["contents"]
            elif module_type == "resource" and "contents" in module:
                content_text = module["contents"]
            elif module_type == "url":
                url = module.get("contents", "")
                content_text = f"URL: {url}"
            
            # Create or update content record
            content = CourseContent.query.filter_by(
                course_id=course_id,
                moodle_module_id=module_id
            ).first()
            
            if not content:
                content = CourseContent(
                    course_id=course_id,
                    title=module_name,
                    content_type=module_type,
                    content_text=content_text,
                    url=url,
                    moodle_module_id=module_id,
                    section_name=section_name
                )
                db.session.add(content)
            else:
                content.title = module_name
                content.content_type = module_type
                content.content_text = content_text
                content.url = url
                content.section_name = section_name
            
            db.session.commit()
            content_count += 1
    
    return content_count
```

### Step 4: Register the Blueprint

Update `main.py` to register the new blueprint:

```python
from routes.moodle_api import moodle_api_bp

app.register_blueprint(moodle_api_bp)
```

### Step 5: Add Moodle Module ID to Content Model

Update `models.py` to add a field for tracking Moodle module IDs:

```python
class CourseContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(256), nullable=False)
    content_type = db.Column(db.String(50))
    content_text = db.Column(db.Text)
    url = db.Column(db.String(512))
    moodle_module_id = db.Column(db.Integer)  # Add this field
    section_name = db.Column(db.String(256))  # Add this field
```

### Step 6: Create Admin Interface for Synchronization

Add a view to the admin dashboard for triggering synchronization:

**templates/admin_dashboard.html** (add section):
```html
<div class="card mb-4">
    <div class="card-header">
        <h5>Moodle Integration</h5>
    </div>
    <div class="card-body">
        <form id="sync-course-form">
            <div class="mb-3">
                <label for="course-id" class="form-label">Moodle Course ID</label>
                <input type="number" class="form-control" id="course-id" required>
            </div>
            <button type="submit" class="btn btn-primary">Sync Course</button>
        </form>
        
        <div class="mt-3" id="sync-result"></div>
        
        <hr>
        
        <h6>Synchronized Courses</h6>
        <table class="table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Title</th>
                    <th>Moodle ID</th>
                    <th>Content Items</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody id="courses-table">
                {% for course in courses %}
                <tr>
                    <td>{{ course.id }}</td>
                    <td>{{ course.title }}</td>
                    <td>{{ course.moodle_course_id }}</td>
                    <td>{{ course.content.count() }}</td>
                    <td>
                        <button class="btn btn-sm btn-primary sync-course-btn" data-course-id="{{ course.moodle_course_id }}">Sync</button>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    const syncForm = document.getElementById('sync-course-form');
    const resultDiv = document.getElementById('sync-result');
    
    syncForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const courseId = document.getElementById('course-id').value;
        syncCourse(courseId);
    });
    
    // Add event listeners for sync buttons
    document.querySelectorAll('.sync-course-btn').forEach(button => {
        button.addEventListener('click', function() {
            const courseId = this.dataset.courseId;
            syncCourse(courseId);
        });
    });
    
    function syncCourse(courseId) {
        resultDiv.innerHTML = '<div class="alert alert-info">Syncing course...</div>';
        
        fetch('/api/moodle/sync-course', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ course_id: courseId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                resultDiv.innerHTML = `
                    <div class="alert alert-success">
                        Successfully synced course: ${data.course.title}<br>
                        Content items: ${data.course.content_items}
                    </div>
                `;
                
                // Refresh the page to show updated data
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            } else {
                resultDiv.innerHTML = `
                    <div class="alert alert-danger">
                        Error: ${data.error || 'Unknown error'}
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            resultDiv.innerHTML = `
                <div class="alert alert-danger">
                    An error occurred. Please try again later.
                </div>
            `;
        });
    }
});
</script>
```

Update the admin dashboard route to pass courses:

```python
@views_bp.route('/admin-dashboard')
def admin_dashboard():
    """Admin dashboard for managing the AI learning assistant"""
    courses = Course.query.all()
    return render_template('admin_dashboard.html', courses=courses)
```

## WebHook-Based Integration

For real-time updates, you can set up webhooks to notify your AI Assistant when events occur in Moodle.

### Step 1: Set Up a Moodle Events Plugin

Create a custom Moodle plugin that sends webhooks when relevant events occur:

**local/ai_assistant_webhooks/version.php**:
```php
<?php
defined('MOODLE_INTERNAL') || die();

$plugin->component = 'local_ai_assistant_webhooks';
$plugin->version = 2025040300;
$plugin->requires = 2022041900; // Moodle 4.0
$plugin->maturity = MATURITY_BETA;
$plugin->release = '0.1.0';
```

**local/ai_assistant_webhooks/settings.php**:
```php
<?php
defined('MOODLE_INTERNAL') || die;

if ($hassiteconfig) {
    $settings = new admin_settingpage('local_ai_assistant_webhooks', get_string('pluginname', 'local_ai_assistant_webhooks'));
    $ADMIN->add('localplugins', $settings);
    
    $settings->add(new admin_setting_configtext(
        'local_ai_assistant_webhooks/webhook_url',
        get_string('webhook_url', 'local_ai_assistant_webhooks'),
        get_string('webhook_url_desc', 'local_ai_assistant_webhooks'),
        '',
        PARAM_URL
    ));
    
    $settings->add(new admin_setting_configpasswordunmask(
        'local_ai_assistant_webhooks/webhook_secret',
        get_string('webhook_secret', 'local_ai_assistant_webhooks'),
        get_string('webhook_secret_desc', 'local_ai_assistant_webhooks'),
        '',
        PARAM_TEXT
    ));
}
```

**local/ai_assistant_webhooks/lang/en/local_ai_assistant_webhooks.php**:
```php
<?php
$string['pluginname'] = 'AI Assistant Webhooks';
$string['webhook_url'] = 'Webhook URL';
$string['webhook_url_desc'] = 'The URL to send webhook events to';
$string['webhook_secret'] = 'Webhook Secret';
$string['webhook_secret_desc'] = 'Secret key used to sign webhook payloads';
```

**local/ai_assistant_webhooks/classes/observer.php**:
```php
<?php
namespace local_ai_assistant_webhooks;

defined('MOODLE_INTERNAL') || die();

class observer {
    /**
     * Send webhook for course created event
     * 
     * @param \core\event\course_created $event
     * @return bool
     */
    public static function course_created(\core\event\course_created $event) {
        return self::send_webhook('course_created', $event);
    }
    
    /**
     * Send webhook for course updated event
     * 
     * @param \core\event\course_updated $event
     * @return bool
     */
    public static function course_updated(\core\event\course_updated $event) {
        return self::send_webhook('course_updated', $event);
    }
    
    /**
     * Send webhook for course module created event
     * 
     * @param \core\event\course_module_created $event
     * @return bool
     */
    public static function course_module_created(\core\event\course_module_created $event) {
        return self::send_webhook('course_module_created', $event);
    }
    
    /**
     * Send webhook for course module updated event
     * 
     * @param \core\event\course_module_updated $event
     * @return bool
     */
    public static function course_module_updated(\core\event\course_module_updated $event) {
        return self::send_webhook('course_module_updated', $event);
    }
    
    /**
     * Send webhook for user enrolled event
     * 
     * @param \core\event\user_enrolment_created $event
     * @return bool
     */
    public static function user_enrolled(\core\event\user_enrolment_created $event) {
        return self::send_webhook('user_enrolled', $event);
    }
    
    /**
     * Send webhook event
     * 
     * @param string $event_type
     * @param \core\event\base $event
     * @return bool
     */
    private static function send_webhook($event_type, \core\event\base $event) {
        $webhook_url = get_config('local_ai_assistant_webhooks', 'webhook_url');
        $webhook_secret = get_config('local_ai_assistant_webhooks', 'webhook_secret');
        
        if (empty($webhook_url)) {
            return false;
        }
        
        // Get event data
        $event_data = $event->get_data();
        
        // Add additional data based on event type
        $additional_data = [];
        
        if ($event_type == 'course_created' || $event_type == 'course_updated') {
            $course = get_course($event_data['objectid']);
            $additional_data['course'] = [
                'id' => $course->id,
                'fullname' => $course->fullname,
                'shortname' => $course->shortname,
                'summary' => $course->summary,
            ];
        } else if ($event_type == 'course_module_created' || $event_type == 'course_module_updated') {
            $cm = get_coursemodule_from_id('', $event_data['objectid']);
            $additional_data['module'] = [
                'id' => $cm->id,
                'course' => $cm->course,
                'name' => $cm->name,
                'modname' => $cm->modname,
                'instance' => $cm->instance,
            ];
        } else if ($event_type == 'user_enrolled') {
            $ue = $event->get_record_snapshot('user_enrolments', $event_data['objectid']);
            $user = \core_user::get_user($ue->userid);
            $additional_data['enrolment'] = [
                'id' => $ue->id,
                'user_id' => $ue->userid,
                'user_email' => $user->email,
                'user_name' => fullname($user),
                'enrolment_id' => $ue->enrolid,
            ];
            
            // Get course ID
            $enrolment = $event->get_record_snapshot('enrol', $ue->enrolid);
            $additional_data['enrolment']['course_id'] = $enrolment->courseid;
        }
        
        // Prepare payload
        $payload = [
            'event_type' => $event_type,
            'timestamp' => time(),
            'moodle_event' => $event_data,
            'data' => $additional_data
        ];
        
        // Generate signature if secret is set
        $signature = '';
        if (!empty($webhook_secret)) {
            $payload_json = json_encode($payload);
            $signature = hash_hmac('sha256', $payload_json, $webhook_secret);
        }
        
        // Send webhook
        $curl = new \curl();
        $curl->setHeader(['Content-Type: application/json']);
        
        if (!empty($signature)) {
            $curl->setHeader(['X-Webhook-Signature: ' . $signature]);
        }
        
        $response = $curl->post($webhook_url, json_encode($payload));
        
        return !empty($response);
    }
}
```

**local/ai_assistant_webhooks/db/events.php**:
```php
<?php
defined('MOODLE_INTERNAL') || die();

$observers = [
    [
        'eventname' => '\core\event\course_created',
        'callback' => '\local_ai_assistant_webhooks\observer::course_created',
    ],
    [
        'eventname' => '\core\event\course_updated',
        'callback' => '\local_ai_assistant_webhooks\observer::course_updated',
    ],
    [
        'eventname' => '\core\event\course_module_created',
        'callback' => '\local_ai_assistant_webhooks\observer::course_module_created',
    ],
    [
        'eventname' => '\core\event\course_module_updated',
        'callback' => '\local_ai_assistant_webhooks\observer::course_module_updated',
    ],
    [
        'eventname' => '\core\event\user_enrolment_created',
        'callback' => '\local_ai_assistant_webhooks\observer::user_enrolled',
    ],
];
```

### Step 2: Create Webhook Endpoint in AI Assistant

Add a webhook endpoint to your AI Assistant application:

**routes/webhooks.py**:
```python
from flask import Blueprint, request, jsonify
import logging
import hmac
import hashlib
import json
import os
from app import db
from models import Course, CourseContent, User

webhook_bp = Blueprint('webhooks', __name__)
logger = logging.getLogger(__name__)

@webhook_bp.route('/api/webhooks/moodle', methods=['POST'])
def moodle_webhook():
    """Receive and process Moodle webhook events"""
    
    # Verify webhook signature if secret is set
    webhook_secret = os.environ.get('WEBHOOK_SECRET')
    
    if webhook_secret:
        signature = request.headers.get('X-Webhook-Signature')
        
        if not signature:
            logger.warning("Webhook received without signature")
            return jsonify({"error": "Signature missing"}), 401
            
        # Compute expected signature
        payload = request.data
        expected_signature = hmac.new(
            webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            logger.warning("Invalid webhook signature")
            return jsonify({"error": "Invalid signature"}), 401
    
    # Process the webhook
    try:
        data = request.json
        event_type = data.get('event_type')
        timestamp = data.get('timestamp')
        event_data = data.get('moodle_event')
        additional_data = data.get('data', {})
        
        logger.info(f"Received Moodle webhook: {event_type}")
        
        # Process different event types
        if event_type == 'course_created' or event_type == 'course_updated':
            process_course_event(event_type, event_data, additional_data)
        elif event_type == 'course_module_created' or event_type == 'course_module_updated':
            process_module_event(event_type, event_data, additional_data)
        elif event_type == 'user_enrolled':
            process_enrollment_event(event_type, event_data, additional_data)
        
        return jsonify({"status": "success"}), 200
    
    except Exception as e:
        logger.exception(f"Error processing webhook: {e}")
        return jsonify({"error": str(e)}), 500

def process_course_event(event_type, event_data, additional_data):
    """Process course created/updated events"""
    course_data = additional_data.get('course', {})
    
    if not course_data:
        logger.warning(f"No course data in {event_type} event")
        return
    
    course_id = course_data.get('id')
    
    # Check if course exists
    course = Course.query.filter_by(moodle_course_id=course_id).first()
    
    if not course and event_type == 'course_created':
        # Create new course
        course = Course(
            moodle_course_id=course_id,
            title=course_data.get('fullname', ''),
            description=course_data.get('summary', '')
        )
        db.session.add(course)
    elif course:
        # Update existing course
        course.title = course_data.get('fullname', course.title)
        course.description = course_data.get('summary', course.description)
    
    db.session.commit()
    logger.info(f"Processed {event_type} for course {course_id}")

def process_module_event(event_type, event_data, additional_data):
    """Process course module created/updated events"""
    module_data = additional_data.get('module', {})
    
    if not module_data:
        logger.warning(f"No module data in {event_type} event")
        return
    
    module_id = module_data.get('id')
    course_id = module_data.get('course')
    
    # Get the course
    course = Course.query.filter_by(moodle_course_id=course_id).first()
    
    if not course:
        logger.warning(f"Course {course_id} not found for module {module_id}")
        return
    
    # Check if module exists
    content = CourseContent.query.filter_by(
        course_id=course.id,
        moodle_module_id=module_id
    ).first()
    
    # This is just a notification - we need to fetch the actual content data
    # For simplicity, just log it - a real implementation would fetch the content
    logger.info(f"Module event {event_type} for module {module_id} in course {course_id}")
    
    # In a real implementation, you would trigger a sync for this specific module:
    # sync_module_content(course_id, module_id)

def process_enrollment_event(event_type, event_data, additional_data):
    """Process user enrollment events"""
    enrollment_data = additional_data.get('enrolment', {})
    
    if not enrollment_data:
        logger.warning(f"No enrollment data in {event_type} event")
        return
    
    user_id = enrollment_data.get('user_id')
    user_email = enrollment_data.get('user_email')
    user_name = enrollment_data.get('user_name')
    course_id = enrollment_data.get('course_id')
    
    # Check if user exists
    user = User.query.filter_by(moodle_user_id=user_id).first()
    
    if not user:
        # Create user
        username = user_email.split('@')[0] if user_email else f"moodle_user_{user_id}"
        
        user = User(
            username=username,
            email=user_email,
            moodle_user_id=user_id,
            # Note: We don't set a password here since auth would be through Moodle
        )
        db.session.add(user)
        db.session.commit()
    
    logger.info(f"Processed enrollment for user {user_id} in course {course_id}")
    
    # In a real implementation, you would create the enrollment record:
    # create_enrollment(user.id, course_id)
```

Register the blueprint in `main.py`:

```python
from routes.webhooks import webhook_bp

app.register_blueprint(webhook_bp)
```

### Step 3: Configure the Webhook in Moodle

After installing the webhook plugin:

1. Go to Site Administration > Plugins > Local plugins > AI Assistant Webhooks
2. Set the Webhook URL to your AI Assistant endpoint (e.g., `https://your-ai-assistant-server.com/api/webhooks/moodle`)
3. Set a secure Webhook Secret and make sure the same value is set as `WEBHOOK_SECRET` in your AI Assistant environment variables

## Single Sign-On (SSO) Configuration

To provide a seamless user experience, you can set up Single Sign-On between Moodle and your AI Assistant.

### Option 1: OAuth 2.0 Integration

#### Step 1: Set Up Moodle as OAuth Provider

1. Go to Site Administration > Plugins > Authentication > OAuth 2 services
2. Click "Configure a custom service"
3. Fill in the service details:
   - Name: "AI Assistant"
   - Client ID: Generate a unique ID
   - Client Secret: Generate a secure secret
   - Service Base URL: The base URL of your Moodle site
   - Login scopes: "openid profile email"
4. Save the service

#### Step 2: Implement OAuth Client in AI Assistant

Add OAuth 2.0 client code to your AI Assistant:

**services/oauth_service.py**:
```python
import os
import requests
from urllib.parse import urlencode
from flask import url_for, session
import secrets
import json

class OAuthService:
    def __init__(self):
        self.client_id = os.environ.get("MOODLE_OAUTH_CLIENT_ID")
        self.client_secret = os.environ.get("MOODLE_OAUTH_CLIENT_SECRET")
        self.moodle_url = os.environ.get("MOODLE_URL")
        self.redirect_uri = os.environ.get("OAUTH_REDIRECT_URI")
    
    def get_authorization_url(self):
        """Generate the authorization URL for OAuth"""
        state = secrets.token_urlsafe(16)
        session['oauth_state'] = state
        
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': 'openid profile email',
            'state': state
        }
        
        auth_url = f"{self.moodle_url}/admin/oauth2/auth.php?{urlencode(params)}"
        return auth_url
    
    def get_token(self, code, state):
        """Exchange authorization code for access token"""
        # Verify state
        if state != session.get('oauth_state'):
            return {'error': 'Invalid state parameter'}
        
        # Exchange code for token
        token_url = f"{self.moodle_url}/admin/oauth2/token.php"
        
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        try:
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            token_data = response.json()
            
            return token_data
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}
    
    def get_user_info(self, access_token):
        """Get user information using the access token"""
        userinfo_url = f"{self.moodle_url}/admin/oauth2/userinfo.php"
        
        headers = {
            'Authorization': f"Bearer {access_token}"
        }
        
        try:
            response = requests.get(userinfo_url, headers=headers)
            response.raise_for_status()
            user_data = response.json()
            
            return user_data
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}
```

Add OAuth routes:

**routes/auth.py**:
```python
from flask import Blueprint, redirect, request, session, url_for, flash
from services.oauth_service import OAuthService
from app import db
from models import User
from flask_login import login_user, logout_user, current_user

auth_bp = Blueprint('auth', __name__)
oauth_service = OAuthService()

@auth_bp.route('/login')
def login():
    """Redirect to Moodle OAuth login"""
    if current_user.is_authenticated:
        return redirect(url_for('views.index'))
    
    auth_url = oauth_service.get_authorization_url()
    return redirect(auth_url)

@auth_bp.route('/oauth/callback')
def oauth_callback():
    """Handle OAuth callback from Moodle"""
    error = request.args.get('error')
    
    if error:
        flash(f"Authentication error: {error}", "danger")
        return redirect(url_for('views.index'))
    
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code:
        flash("No authorization code received", "danger")
        return redirect(url_for('views.index'))
    
    # Exchange code for token
    token_data = oauth_service.get_token(code, state)
    
    if 'error' in token_data:
        flash(f"Token error: {token_data['error']}", "danger")
        return redirect(url_for('views.index'))
    
    # Get user info
    user_info = oauth_service.get_user_info(token_data['access_token'])
    
    if 'error' in user_info:
        flash(f"User info error: {user_info['error']}", "danger")
        return redirect(url_for('views.index'))
    
    # Find or create user
    email = user_info.get('email')
    moodle_user_id = user_info.get('id')
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        user = User(
            username=email.split('@')[0],
            email=email,
            moodle_user_id=moodle_user_id
        )
        db.session.add(user)
        db.session.commit()
    
    # Log in the user
    login_user(user)
    
    # Save token in session for API calls
    session['access_token'] = token_data['access_token']
    session['refresh_token'] = token_data.get('refresh_token')
    
    return redirect(url_for('views.index'))

@auth_bp.route('/logout')
def logout():
    """Log out the user"""
    logout_user()
    session.pop('access_token', None)
    session.pop('refresh_token', None)
    return redirect(url_for('views.index'))
```

Register the blueprint in `main.py`:

```python
from routes.auth import auth_bp

app.register_blueprint(auth_bp)
```

### Option 2: Moodle API Authentication

For a simpler approach, you can use Moodle's login API:

**routes/auth.py** (alternative):
```python
from flask import Blueprint, request, redirect, url_for, flash, render_template
from app import db
from models import User
from flask_login import login_user, logout_user
import requests
import os

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login form and handler"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash("Please enter both username and password", "danger")
            return render_template('login.html')
        
        # Authenticate with Moodle
        auth_result = authenticate_with_moodle(username, password)
        
        if 'error' in auth_result:
            flash(f"Authentication error: {auth_result['error']}", "danger")
            return render_template('login.html')
        
        # User authenticated, find or create user
        user = User.query.filter_by(moodle_user_id=auth_result['user_id']).first()
        
        if not user:
            user = User(
                username=username,
                email=auth_result.get('email', ''),
                moodle_user_id=auth_result['user_id']
            )
            db.session.add(user)
            db.session.commit()
        
        login_user(user)
        return redirect(url_for('views.index'))
    
    return render_template('login.html')

def authenticate_with_moodle(username, password):
    """Authenticate with Moodle login API"""
    moodle_url = os.environ.get("MOODLE_URL")
    
    if not moodle_url:
        return {'error': 'MOODLE_URL not configured'}
    
    # Use Moodle login API
    login_url = f"{moodle_url}/login/token.php"
    
    data = {
        'username': username,
        'password': password,
        'service': 'moodle_mobile_app'
    }
    
    try:
        response = requests.post(login_url, data=data)
        response.raise_for_status()
        result = response.json()
        
        if 'error' in result:
            return {'error': result['error']}
        
        if 'token' not in result:
            return {'error': 'No token received'}
        
        # Get user info using the token
        user_info = get_user_info(result['token'])
        
        return {
            'token': result['token'],
            'user_id': user_info.get('id'),
            'email': user_info.get('email')
        }
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def get_user_info(token):
    """Get user info using Moodle API token"""
    moodle_url = os.environ.get("MOODLE_URL")
    
    api_url = f"{moodle_url}/webservice/rest/server.php"
    
    params = {
        'wstoken': token,
        'wsfunction': 'core_webservice_get_site_info',
        'moodlewsrestformat': 'json'
    }
    
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return {}

@auth_bp.route('/logout')
def logout():
    """Log out the user"""
    logout_user()
    return redirect(url_for('views.index'))
```

Create a login template:

**templates/login.html**:
```html
{% extends "base.html" %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5>Login with Moodle Credentials</h5>
            </div>
            <div class="card-body">
                <form method="POST">
                    <div class="mb-3">
                        <label for="username" class="form-label">Username</label>
                        <input type="text" class="form-control" id="username" name="username" required>
                    </div>
                    <div class="mb-3">
                        <label for="password" class="form-label">Password</label>
                        <input type="password" class="form-control" id="password" name="password" required>
                    </div>
                    <button type="submit" class="btn btn-primary">Login</button>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

## Data Synchronization Strategies

### Approaches to Data Synchronization

1. **On-Demand Synchronization**:
   - Sync data when explicitly requested by an admin
   - Best for initial setup or occasional updates
   - Implemented using admin dashboard controls

2. **Scheduled Synchronization**:
   - Regularly sync data on a fixed schedule
   - Good for keeping data fresh without real-time requirements
   - Implemented using background tasks or cron jobs

3. **Event-Driven Synchronization**:
   - Sync data in response to specific events (via webhooks)
   - Best for real-time updates and immediate consistency
   - Implemented using the webhook integration

4. **Hybrid Approach**:
   - Combine multiple strategies based on data type and update frequency
   - Most comprehensive but more complex to implement

### Sample Scheduled Sync Implementation

**services/sync_service.py**:
```python
import logging
from datetime import datetime
from app import db
from models import Course, CourseContent, User
from services.moodle_api_client import MoodleAPIClient

class SyncService:
    def __init__(self):
        self.moodle_client = MoodleAPIClient()
        self.logger = logging.getLogger(__name__)
    
    def sync_all_courses(self):
        """Synchronize all courses from Moodle"""
        try:
            courses = self.moodle_client.get_courses()
            
            if isinstance(courses, dict) and 'error' in courses:
                self.logger.error(f"Error fetching courses: {courses['error']}")
                return {
                    'success': False,
                    'error': courses['error'],
                    'courses_synced': 0
                }
            
            courses_synced = 0
            
            for course_data in courses:
                result = self.sync_course(course_data['id'])
                
                if result.get('success'):
                    courses_synced += 1
            
            return {
                'success': True,
                'courses_synced': courses_synced,
                'total_courses': len(courses)
            }
        
        except Exception as e:
            self.logger.exception(f"Error in sync_all_courses: {e}")
            return {
                'success': False,
                'error': str(e),
                'courses_synced': 0
            }
    
    def sync_course(self, course_id):
        """Synchronize a specific course from Moodle"""
        try:
            # Get course data from Moodle
            course_data = self.moodle_client.call_api("core_course_get_courses", {"ids": [course_id]})
            
            if isinstance(course_data, dict) and 'error' in course_data:
                self.logger.error(f"Error fetching course {course_id}: {course_data['error']}")
                return {
                    'success': False,
                    'error': course_data['error']
                }
            
            if not course_data or not isinstance(course_data, list) or len(course_data) == 0:
                return {
                    'success': False,
                    'error': 'Course not found'
                }
            
            # Get course content
            content_data = self.moodle_client.call_api("core_course_get_contents", {"courseid": course_id})
            
            if isinstance(content_data, dict) and 'error' in content_data:
                self.logger.error(f"Error fetching content for course {course_id}: {content_data['error']}")
                return {
                    'success': False,
                    'error': content_data['error']
                }
            
            # Process course data
            course_info = course_data[0]
            
            # Create or update course record
            course = Course.query.filter_by(moodle_course_id=course_info["id"]).first()
            
            if not course:
                course = Course(
                    moodle_course_id=course_info["id"],
                    title=course_info["fullname"],
                    description=course_info.get("summary", ""),
                    last_synced=datetime.utcnow()
                )
                db.session.add(course)
                db.session.commit()
            else:
                course.title = course_info["fullname"]
                course.description = course_info.get("summary", "")
                course.last_synced = datetime.utcnow()
                db.session.commit()
            
            # Process content
            content_count = self._process_course_content(course.id, content_data)
            
            return {
                'success': True,
                'course': {
                    'id': course.id,
                    'moodle_id': course.moodle_course_id,
                    'title': course.title,
                    'content_items': content_count
                }
            }
        
        except Exception as e:
            self.logger.exception(f"Error syncing course {course_id}: {e}")
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _process_course_content(self, course_id, content_data):
        """Process and store course content"""
        content_count = 0
        
        for section in content_data:
            section_name = section.get("name")
            
            for module in section.get("modules", []):
                if not module.get("name"):
                    continue
                    
                module_name = module.get("name")
                module_type = module.get("modname")
                module_id = module.get("id")
                
                content_text = ""
                url = ""
                
                # Extract content based on module type
                if module_type == "page" and "contents" in module:
                    content_text = module["contents"]
                elif module_type == "resource" and "contents" in module:
                    content_text = module["contents"]
                elif module_type == "url":
                    url = module.get("contents", "")
                    content_text = f"URL: {url}"
                
                # Create or update content record
                content = CourseContent.query.filter_by(
                    course_id=course_id,
                    moodle_module_id=module_id
                ).first()
                
                if not content:
                    content = CourseContent(
                        course_id=course_id,
                        title=module_name,
                        content_type=module_type,
                        content_text=content_text,
                        url=url,
                        moodle_module_id=module_id,
                        section_name=section_name,
                        last_synced=datetime.utcnow()
                    )
                    db.session.add(content)
                else:
                    content.title = module_name
                    content.content_type = module_type
                    content.content_text = content_text
                    content.url = url
                    content.section_name = section_name
                    content.last_synced = datetime.utcnow()
                
                db.session.commit()
                content_count += 1
        
        return content_count
    
    def sync_users(self, course_id=None):
        """Synchronize users from Moodle"""
        try:
            if course_id:
                # Sync users for a specific course
                users_data = self.moodle_client.get_course_users(course_id)
            else:
                # Sync all users (this would require admin capabilities)
                users_data = self.moodle_client.call_api("core_user_get_users", {"criteria": [{"key": "auth", "value": "manual"}]})
            
            if isinstance(users_data, dict) and 'error' in users_data:
                self.logger.error(f"Error fetching users: {users_data['error']}")
                return {
                    'success': False,
                    'error': users_data['error'],
                    'users_synced': 0
                }
            
            users_synced = 0
            
            for user_data in users_data:
                # Create or update user
                user = User.query.filter_by(moodle_user_id=user_data["id"]).first()
                
                if not user:
                    user = User(
                        username=user_data.get("username"),
                        email=user_data.get("email"),
                        moodle_user_id=user_data["id"],
                        last_synced=datetime.utcnow()
                    )
                    db.session.add(user)
                else:
                    user.username = user_data.get("username", user.username)
                    user.email = user_data.get("email", user.email)
                    user.last_synced = datetime.utcnow()
                
                db.session.commit()
                users_synced += 1
            
            return {
                'success': True,
                'users_synced': users_synced,
                'total_users': len(users_data)
            }
        
        except Exception as e:
            self.logger.exception(f"Error syncing users: {e}")
            db.session.rollback()
            return {
                'success': False,
                'error': str(e),
                'users_synced': 0
            }
```

Add a scheduler for background sync:

**scheduler.py**:
```python
import atexit
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from services.sync_service import SyncService

sync_service = SyncService()
logger = logging.getLogger(__name__)

def start_scheduler():
    """Start the background scheduler for periodic tasks"""
    scheduler = BackgroundScheduler()
    
    # Sync all courses every 6 hours
    scheduler.add_job(
        func=sync_all_courses_job,
        trigger=IntervalTrigger(hours=6),
        id='sync_all_courses',
        name='Sync all courses from Moodle',
        replace_existing=True
    )
    
    scheduler.start()
    
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
    
    return scheduler

def sync_all_courses_job():
    """Background job to sync all courses"""
    logger.info("Starting scheduled sync of all courses")
    
    try:
        result = sync_service.sync_all_courses()
        
        if result.get('success'):
            logger.info(f"Scheduled sync completed successfully. Synced {result.get('courses_synced')} of {result.get('total_courses')} courses.")
        else:
            logger.error(f"Scheduled sync failed: {result.get('error')}")
    
    except Exception as e:
        logger.exception(f"Exception in scheduled sync job: {e}")
```

Initialize the scheduler in `main.py`:

```python
from scheduler import start_scheduler

# Start the background scheduler
scheduler = start_scheduler()
```

## Troubleshooting Common Issues

### Integration Issues

1. **Authentication Failures**
   - Verify that API tokens and credentials are correct
   - Check that user permissions are set correctly in Moodle
   - Ensure that web services are enabled in Moodle

2. **CORS Issues**
   - Set appropriate CORS headers in your AI Assistant API
   - Try using server-side requests instead of browser-based requests
   - Consider using a proxy through Moodle if needed

3. **Plugin Installation Errors**
   - Ensure your plugin follows Moodle's plugin structure
   - Check compatibility with your Moodle version
   - Verify file permissions on the server

### Data Synchronization Issues

1. **Missing or Incomplete Data**
   - Verify that your API requests include all required parameters
   - Check that the user token has sufficient permissions
   - Enable more detailed logging to trace the data flow

2. **Performance Problems**
   - Implement incremental synchronization instead of full syncs
   - Add caching for frequently accessed data
   - Optimize database queries and indexes

3. **Error Handling**
   - Implement robust error handling and retry mechanisms
   - Set up monitoring and alerts for failed synchronizations
   - Create a manual sync option in the admin interface

### Widget Embedding Issues

1. **JavaScript Conflicts**
   - Use namespaced code to avoid conflicts with Moodle's JavaScript
   - Consider using iframes for complete isolation
   - Test with different Moodle themes

2. **Styling Problems**
   - Use scoped CSS to prevent style leakage
   - Test with different Moodle themes
   - Consider using Shadow DOM for complete style isolation

3. **Responsive Design Issues**
   - Test your widget on various screen sizes
   - Implement breakpoints that align with Moodle's responsive design
   - Use relative units (em, rem) instead of pixels