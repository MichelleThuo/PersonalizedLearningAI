/**
 * Moodle LMS Integration Service
 * Handles communication between our application and the Moodle LMS API
 */

// Main Moodle API integration class
class MoodleIntegration {
  constructor(baseUrl, token) {
    this.baseUrl = baseUrl;
    this.token = token;
    this.wsEndpoint = `${baseUrl}/webservice/rest/server.php`;
  }

  /**
   * Make a request to the Moodle API
   * @param {string} wsfunction - The web service function to call
   * @param {Object} params - Additional parameters for the function
   * @returns {Promise<Object>} - API response
   */
  async callMoodleApi(wsfunction, params = {}) {
    try {
      // Build request parameters
      const requestParams = new URLSearchParams({
        wstoken: this.token,
        wsfunction: wsfunction,
        moodlewsrestformat: 'json',
        ...params
      });

      // Make request to Moodle API
      const response = await fetch(`${this.wsEndpoint}?${requestParams}`);
      
      if (!response.ok) {
        throw new Error(`Moodle API error: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Check for Moodle exception
      if (data && data.exception) {
        throw new Error(`Moodle exception: ${data.message}`);
      }
      
      return data;
    } catch (error) {
      console.error('Moodle API call failed:', error);
      throw error;
    }
  }

  /**
   * Get user courses from Moodle
   * @param {number} userId - Moodle user ID
   * @returns {Promise<Array>} - List of courses
   */
  async getUserCourses(userId) {
    return this.callMoodleApi('core_enrol_get_users_courses', { userid: userId });
  }

  /**
   * Get course content
   * @param {number} courseId - Moodle course ID
   * @returns {Promise<Array>} - Course content
   */
  async getCourseContent(courseId) {
    return this.callMoodleApi('core_course_get_contents', { courseid: courseId });
  }

  /**
   * Search for courses
   * @param {string} keyword - Search keyword
   * @returns {Promise<Array>} - Search results
   */
  async searchCourses(keyword) {
    return this.callMoodleApi('core_course_search_courses', { criterianame: 'search', criteriavalue: keyword });
  }

  /**
   * Get user profile
   * @param {number} userId - Moodle user ID
   * @returns {Promise<Object>} - User profile
   */
  async getUserProfile(userId) {
    const users = await this.callMoodleApi('core_user_get_users_by_field', { 
      field: 'id', 
      values: [userId] 
    });
    return users[0];
  }

  /**
   * Synchronize course data from Moodle to our local database
   * @param {number} courseId - Moodle course ID
   * @returns {Promise<Object>} - Sync result
   */
  async syncCourseToDatabase(courseId) {
    try {
      // Get course content from Moodle
      const courseContent = await this.getCourseContent(courseId);
      
      // Send to our backend for processing and storage
      const response = await fetch('/api/moodle/sync-course', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          course_id: courseId,
          content: courseContent
        })
      });
      
      if (!response.ok) {
        throw new Error(`Failed to sync course: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Course sync failed:', error);
      throw error;
    }
  }

  /**
   * Get user completion status for a course
   * @param {number} userId - Moodle user ID
   * @param {number} courseId - Moodle course ID
   * @returns {Promise<Object>} - Completion status
   */
  async getCourseCompletion(userId, courseId) {
    return this.callMoodleApi('core_completion_get_course_completion_status', {
      userid: userId,
      courseid: courseId
    });
  }

  /**
   * Get grades for a specific course
   * @param {number} userId - Moodle user ID
   * @param {number} courseId - Moodle course ID
   * @returns {Promise<Object>} - User grades
   */
  async getUserGrades(userId, courseId) {
    return this.callMoodleApi('gradereport_user_get_grade_items', {
      userid: userId,
      courseid: courseId
    });
  }
}

// Utility functions for Moodle content processing
const MoodleUtils = {
  /**
   * Extract text content from Moodle HTML
   * @param {string} html - HTML content from Moodle
   * @returns {string} - Plain text content
   */
  extractTextFromHtml(html) {
    // Create a temporary element to parse HTML
    const temp = document.createElement('div');
    temp.innerHTML = html;
    return temp.textContent || temp.innerText || '';
  },

  /**
   * Parse Moodle module types from course contents
   * @param {Array} courseContents - Moodle course contents
   * @returns {Object} - Organized content by type
   */
  organizeContentByType(courseContents) {
    const organized = {
      documents: [],
      videos: [],
      quizzes: [],
      assignments: [],
      others: []
    };
    
    if (!courseContents || !Array.isArray(courseContents)) {
      return organized;
    }
    
    courseContents.forEach(section => {
      if (section.modules && Array.isArray(section.modules)) {
        section.modules.forEach(module => {
          const moduleType = module.modname;
          
          const contentItem = {
            id: module.id,
            name: module.name,
            type: moduleType,
            url: module.url || '',
            content: '',
            section: section.name,
            sectionId: section.id
          };
          
          // Process content based on module type
          switch (moduleType) {
            case 'resource':
              organized.documents.push(contentItem);
              break;
            case 'url':
            case 'page':
              // Extract if it's a video URL
              if (module.url && (module.url.includes('youtube') || 
                                 module.url.includes('vimeo') || 
                                 module.url.includes('mp4'))) {
                organized.videos.push(contentItem);
              } else {
                organized.documents.push(contentItem);
              }
              break;
            case 'quiz':
              organized.quizzes.push(contentItem);
              break;
            case 'assign':
              organized.assignments.push(contentItem);
              break;
            default:
              organized.others.push(contentItem);
          }
        });
      }
    });
    
    return organized;
  },
  
  /**
   * Extract searchable content from Moodle course
   * @param {Array} courseContents - Moodle course contents
   * @returns {Array} - Searchable content items with extracted text
   */
  extractSearchableContent(courseContents) {
    const searchableItems = [];
    
    if (!courseContents || !Array.isArray(courseContents)) {
      return searchableItems;
    }
    
    courseContents.forEach(section => {
      if (section.modules && Array.isArray(section.modules)) {
        section.modules.forEach(module => {
          // Extract text content from module
          let textContent = module.name;
          
          if (module.description) {
            textContent += ' ' + this.extractTextFromHtml(module.description);
          }
          
          if (module.contents && Array.isArray(module.contents)) {
            module.contents.forEach(content => {
              if (content.type === 'file' && content.mimetype.includes('text')) {
                textContent += ' ' + this.extractTextFromHtml(content.content || '');
              }
            });
          }
          
          searchableItems.push({
            id: module.id,
            name: module.name,
            type: module.modname,
            content: textContent.trim(),
            url: module.url || ''
          });
        });
      }
    });
    
    return searchableItems;
  }
};

// Initialize Moodle integration when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  // Configuration will be loaded from server or environment
  const moodleConfigElement = document.getElementById('moodle-config');
  
  if (moodleConfigElement) {
    try {
      const moodleConfig = JSON.parse(moodleConfigElement.textContent);
      
      // Initialize Moodle integration
      window.moodleIntegration = new MoodleIntegration(
        moodleConfig.baseUrl,
        moodleConfig.token
      );
      
      console.log('Moodle integration initialized successfully');
    } catch (error) {
      console.error('Failed to initialize Moodle integration:', error);
    }
  }
});

// Export for modular usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    MoodleIntegration,
    MoodleUtils
  };
}