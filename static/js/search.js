// Search functionality
document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.getElementById('search-form');
    const searchInput = document.getElementById('search-input');
    const searchResults = document.getElementById('search-results');
    const courseSelect = document.getElementById('course-select');
    
    // Function to perform search
    function performSearch(query, courseId = null) {
        // Clear previous results
        searchResults.innerHTML = '';
        
        // Show loading state
        searchResults.innerHTML = `
            <div class="loading-container">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p>Searching for results...</p>
            </div>
        `;
        
        // Build the URL with query parameters
        let url = `/api/search?q=${encodeURIComponent(query)}`;
        if (courseId) {
            url += `&course_id=${courseId}`;
        }
        
        // Fetch search results from API
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                displaySearchResults(data.results);
            })
            .catch(error => {
                searchResults.innerHTML = `
                    <div class="alert alert-danger" role="alert">
                        Error: ${error.message}. Please try again.
                    </div>
                `;
                console.error('Error performing search:', error);
            });
    }
    
    // Function to display search results
    function displaySearchResults(results) {
        // Clear results container
        searchResults.innerHTML = '';
        
        if (results.length === 0) {
            searchResults.innerHTML = `
                <div class="alert alert-info" role="alert">
                    No results found. Try a different search term.
                </div>
            `;
            return;
        }
        
        // Create results list
        const resultsList = document.createElement('div');
        resultsList.className = 'list-group mt-3';
        
        // Add results to list
        results.forEach(result => {
            const resultItem = document.createElement('div');
            resultItem.className = 'list-group-item';
            
            // Determine icon based on content type
            let icon = 'fa-file-alt'; // Default icon
            if (result.content_type === 'video') {
                icon = 'fa-video';
            } else if (result.content_type === 'quiz') {
                icon = 'fa-question-circle';
            } else if (result.content_type === 'document') {
                icon = 'fa-file-pdf';
            }
            
            // Create result item HTML
            resultItem.innerHTML = `
                <div class="d-flex">
                    <div class="flex-shrink-0 me-3">
                        <i class="fas ${icon} fa-2x text-primary"></i>
                    </div>
                    <div class="flex-grow-1">
                        <h5 class="mt-0">${result.title}</h5>
                        <p>${result.snippet || 'No preview available'}</p>
                        ${result.url ? `<a href="${result.url}" target="_blank" class="btn btn-sm btn-primary">View Content</a>` : ''}
                        <button class="btn btn-sm btn-outline-primary ms-2 chat-about-btn" data-title="${result.title}">
                            <i class="fas fa-comments"></i> Chat about this
                        </button>
                    </div>
                </div>
            `;
            
            resultsList.appendChild(resultItem);
        });
        
        searchResults.appendChild(resultsList);
        
        // Add click handlers for "Chat about this" buttons
        document.querySelectorAll('.chat-about-btn').forEach(button => {
            button.addEventListener('click', function() {
                const title = this.dataset.title;
                window.location.href = `/chat?prompt=${encodeURIComponent(`Tell me about ${title}`)}`;
            });
        });
    }
    
    // Handle search form submission
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const query = searchInput.value.trim();
            if (!query) return;
            
            // Get selected course ID if available
            const courseId = courseSelect ? courseSelect.value : null;
            
            // Update URL with search parameters (for bookmarking/sharing)
            const searchParams = new URLSearchParams(window.location.search);
            searchParams.set('q', query);
            if (courseId) {
                searchParams.set('course_id', courseId);
            } else {
                searchParams.delete('course_id');
            }
            
            const newUrl = `${window.location.pathname}?${searchParams.toString()}`;
            window.history.pushState({}, '', newUrl);
            
            // Perform the search
            performSearch(query, courseId);
        });
    }
    
    // Initial search if query params exist
    const urlParams = new URLSearchParams(window.location.search);
    const initialQuery = urlParams.get('q');
    const initialCourseId = urlParams.get('course_id');
    
    if (initialQuery) {
        searchInput.value = initialQuery;
        
        if (courseSelect && initialCourseId) {
            courseSelect.value = initialCourseId;
        }
        
        performSearch(initialQuery, initialCourseId);
    }
    
    // Handle course selection change
    if (courseSelect) {
        courseSelect.addEventListener('change', function() {
            const query = searchInput.value.trim();
            if (query) {
                performSearch(query, this.value);
                
                // Update URL with selected course
                const searchParams = new URLSearchParams(window.location.search);
                searchParams.set('course_id', this.value);
                const newUrl = `${window.location.pathname}?${searchParams.toString()}`;
                window.history.pushState({}, '', newUrl);
            }
        });
    }
});
