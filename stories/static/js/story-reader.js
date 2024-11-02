class StoryReader {
    constructor() {
        console.log('StoryReader initialized');
        this.currentStory = null;
        this.currentChapter = null;
        this.currentParagraphId = null;
        this.viewedParagraphs = new Set();
        
        console.log('Checking for generate button...');
        const generateButton = document.getElementById('generateParagraphButton');
        console.log('Generate button exists:', !!generateButton);
        
        this.init();
        this.setupGenerateParagraphButton();
    }

    init() {
        this.fetchStories();
        this.setupEventListeners();
        this.handleUrlParameters();
    }

    setupEventListeners() {
        document.getElementById('backButton').addEventListener('click', () => this.showStoryList());
    }

    async fetchStories() {
        try {
            console.log('Fetching stories...');
            const response = await fetch('/stories/api/stories/');
            const stories = await response.json();
            console.log('Stories received:', stories);
            this.renderStories(stories);
        } catch (error) {
            console.error('Error fetching stories:', error);
        }
    }

    renderStories(stories) {
        const grid = document.getElementById('storiesGrid');
        const template = document.getElementById('storyCardTemplate');
        
        grid.innerHTML = '';
        stories.forEach(story => {
            const clone = template.content.cloneNode(true);
            const card = clone.querySelector('div');
            
            card.querySelector('h3').textContent = story.title;
            card.querySelector('p').textContent = story.description;
            card.querySelector('button').addEventListener('click', () => this.selectStory(story));
            
            grid.appendChild(card);
        });
    }

    async selectStory(story) {
        this.currentStory = story;
        document.getElementById('storyListView').classList.add('hidden');
        document.getElementById('storyReadingView').classList.remove('hidden');
        document.getElementById('storyTitle').textContent = story.title;

        await this.fetchChapters(story.id);
        await this.fetchReadingProgress();
    }

    async fetchChapters(storyId) {
        try {
            const response = await fetch(`/stories/api/stories/${storyId}/chapters/`);
            const chapters = await response.json();
            this.renderChapters(chapters);
        } catch (error) {
            console.error('Error fetching chapters:', error);
        }
    }

    renderChapters(chapters) {
        const nav = document.getElementById('chapterNav');
        nav.innerHTML = '';
        
        chapters.forEach(chapter => {
            const button = document.createElement('button');
            button.textContent = `Chapter ${chapter.chapter_number}: ${chapter.title}`;
            button.className = 'text-left px-4 py-2 rounded-md transition-colors duration-200 ' +
                              'hover:bg-indigo-600 hover:text-white focus:outline-none focus:ring-2 ' +
                              'focus:ring-indigo-500 focus:ring-offset-2';
            
            // Add data attribute for easier state management
            button.dataset.chapterId = chapter.id;
            
            // Set initial state
            this.updateChapterButtonState(button, chapter === this.currentChapter);
            
            button.addEventListener('click', () => this.selectChapter(chapter));
            nav.appendChild(button);
        });
    }

    updateChapterButtonState(button, isActive) {
        if (isActive) {
            button.classList.add('bg-indigo-600', 'text-white');
            button.classList.remove('bg-gray-100', 'text-gray-700');
            // Add aria-current for accessibility
            button.setAttribute('aria-current', 'true');
        } else {
            button.classList.add('bg-gray-100', 'text-gray-700');
            button.classList.remove('bg-indigo-600', 'text-white');
            button.removeAttribute('aria-current');
        }
    }

    async selectChapter(chapter, page = 1) {
        this.currentChapter = chapter;
        this.updateChapterUI(chapter);
        
        // Update URL with page parameter
        this.updateUrl({
            story: this.currentStory.id,
            chapter: chapter.id,
            page: page
        });
        
        // Fetch paragraphs for the specific page
        await this.fetchParagraphs(chapter.id, page);
        await this.updateReadingProgress();
    }

    updateChapterUI(chapter) {
        document.getElementById('currentChapterDisplay').textContent = 
            `Current Chapter: ${chapter.chapter_number}: ${chapter.title}`;
        
        // Update chapter button states
        const buttons = document.getElementById('chapterNav').children;
        Array.from(buttons).forEach(button => {
            const isCurrentChapter = button.dataset.chapterId === chapter.id.toString();
            this.updateChapterButtonState(button, isCurrentChapter);
        });
    }

    async fetchParagraphs(chapterId, page = 1) {
        try {
            const response = await fetch(`/stories/api/chapters/${chapterId}/paragraphs/?page=${page}`);
            const data = await response.json();
            this.renderParagraphs(data.results, data.has_next);
            return data.results;
        } catch (error) {
            console.error('Error fetching paragraphs:', error);
        }
    }

    renderParagraphs(paragraphs, hasNext) {
        const container = document.getElementById('paragraphsContainer');
        container.innerHTML = ''; // Clear existing content
        
        // Render paragraphs
        paragraphs.forEach(paragraph => {
            const paragraphDiv = document.createElement('div');
            paragraphDiv.id = `paragraph-${paragraph.id}`;
            paragraphDiv.className = 'mb-6 p-4 bg-white rounded-lg shadow';
            
            if (paragraph.is_locked) {
                paragraphDiv.innerHTML = `
                    <div class="text-center py-8">
                        <svg class="w-12 h-12 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                  d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                        </svg>
                        <p class="text-gray-600 mb-4">This paragraph is locked</p>
                        <button class="bg-green-600 text-white px-6 py-2 rounded-md hover:bg-green-700 
                                   transition-colors duration-200">
                            Unlock for ${paragraph.unlock_price} USDC
                        </button>
                    </div>
                `;
                paragraphDiv.querySelector('button').addEventListener('click', 
                    () => this.unlockParagraph(paragraph));
            } else {
                paragraphDiv.innerHTML = `
                    <div class="paragraph-content prose">
                        ${paragraph.text}
                    </div>
                `;
            }
            
            paragraphDiv.addEventListener('click', () => this.handleParagraphClick(paragraph));
            container.appendChild(paragraphDiv);
        });

        // Add navigation buttons
        const currentPage = parseInt(new URLSearchParams(window.location.search).get('page')) || 1;
        const navButtons = document.createElement('div');
        navButtons.className = 'flex justify-between mt-4';
        navButtons.innerHTML = `
            <button id="prevPage" class="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 
                                       transition-colors duration-200 ${currentPage <= 1 ? 'opacity-50 cursor-not-allowed' : ''}">
                Previous Page
            </button>
            <button id="nextPage" class="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 
                                       transition-colors duration-200">
                ${hasNext ? 'Next Page' : 'Create Next Page'}
            </button>
        `;
        container.appendChild(navButtons);

        // Add event listeners to navigation buttons
        const prevButton = navButtons.querySelector('#prevPage');
        const nextButton = navButtons.querySelector('#nextPage');
        
        if (currentPage > 1) {
            prevButton.addEventListener('click', () => this.navigateToPage('prev'));
        }
        
        if (hasNext) {
            nextButton.addEventListener('click', () => this.navigateToPage('next'));
        } else {
            nextButton.addEventListener('click', () => this.generateNextPage());
        }
    }

    async unlockParagraph(paragraph) {
        try {
            const response = await fetch(`/stories/api/paragraphs/${paragraph.id}/unlock/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({ amount: paragraph.unlock_price })
            });
            
            if (response.ok) {
                await this.fetchParagraphs(this.currentChapter.id);
            }
        } catch (error) {
            console.error('Error unlocking paragraph:', error);
        }
    }

    showStoryList() {
        document.getElementById('storyReadingView').classList.add('hidden');
        document.getElementById('storyListView').classList.remove('hidden');
        this.currentStory = null;
        this.currentChapter = null;
    }

    async fetchReadingProgress() {
        try {
            const response = await fetch(`/stories/api/reading-progress/?story=${this.currentStory.id}`);
            const progress = await response.json();
            if (progress.length > 0) {
                this.updateProgressBar(progress[0]);
            }
        } catch (error) {
            console.error('Error fetching reading progress:', error);
        }
    }

    async updateReadingProgress() {
        try {
            await fetch('/stories/api/reading-progress/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({
                    story: this.currentStory.id,
                    current_chapter: this.currentChapter?.id,
                    current_paragraph: this.currentParagraphId
                })
            });
        } catch (error) {
            console.error('Error updating reading progress:', error);
        }
    }

    updateProgressBar(progress) {
        const progressBar = document.getElementById('progressBar');
        const percentage = this.calculateProgress(progress);
        progressBar.style.width = `${percentage}%`;
    }

    calculateProgress(progress) {
        // Implement progress calculation logic here
        return 0; // Placeholder
    }

    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    handleUrlParameters() {
        const urlParams = new URLSearchParams(window.location.search);
        const storyId = urlParams.get('story');
        const chapterId = urlParams.get('chapter');
        const paragraphId = urlParams.get('paragraph');
        const page = urlParams.get('page') || '1';

        if (storyId) {
            this.loadFromUrlParams(storyId, chapterId, paragraphId, page);
        }
    }

    async loadFromUrlParams(storyId, chapterId, paragraphId, page) {
        try {
            // Load story
            const storyResponse = await fetch(`/stories/api/stories/${storyId}/`);
            const story = await storyResponse.json();
            await this.selectStory(story);

            // Load chapter if specified
            if (chapterId) {
                const chapterResponse = await fetch(`/stories/api/chapters/${chapterId}/`);
                const chapter = await chapterResponse.json();
                await this.selectChapter(chapter, page);
            }

            // Load paragraph if specified
            if (paragraphId) {
                const paragraphResponse = await fetch(`/stories/api/paragraphs/${paragraphId}/`);
                const paragraph = await paragraphResponse.json();
                this.scrollToParagraph(paragraphId);
                await this.markParagraphAsViewed(paragraphId);
                
                // Ensure navigation history is loaded and positioned correctly
                await this.loadNavigationHistory();
            }
        } catch (error) {
            console.error('Error loading from URL parameters:', error);
        }
    }

    async handleParagraphClick(paragraph) {
        this.currentParagraphId = paragraph.id;
        this.viewedParagraphs.add(paragraph.id);
        
        // Update URL with all parameters
        this.updateUrl({
            story: this.currentStory.id,
            chapter: this.currentChapter.id,
            paragraph: paragraph.id,
            page: paragraph.page
        });
        
        // Record the view in the database
        await this.recordView({
            story: this.currentStory.id,
            chapter: this.currentChapter.id,
            paragraph: paragraph.id
        });
        
        // Add to navigation history
        this.addToHistory({
            story: this.currentStory.id,
            chapter: this.currentChapter.id,
            paragraph: paragraph.id
        });
    }

    async recordView({ story, chapter, paragraph }) {
        try {
            const response = await fetch('/stories/api/reading-progress/mark_viewed/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({
                    story: story,
                    chapter: chapter,
                    paragraph: paragraph
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to record view');
            }
            
            this.viewedParagraphs.add(paragraph);
        } catch (error) {
            console.error('Error recording view:', error);
        }
    }

    updateUrl({ story, chapter, paragraph = null, page = 1 }) {
        const url = new URL(window.location);
        url.searchParams.set('story', story);
        url.searchParams.set('chapter', chapter);
        url.searchParams.set('page', page);
        
        if (paragraph) {
            url.searchParams.set('paragraph', paragraph);
        } else {
            url.searchParams.delete('paragraph');
        }
        
        window.history.pushState(
            { story, chapter, paragraph, page }, 
            '', 
            url
        );
    }

    async markParagraphAsViewed(paragraphId) {
        try {
            const response = await fetch('/stories/api/reading-progress/mark_viewed/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({
                    story: this.currentStory.id,
                    paragraph: paragraphId
                })
            });

            if (!response.ok) {
                throw new Error('Failed to mark paragraph as viewed');
            }

            this.viewedParagraphs.add(paragraphId);
        } catch (error) {
            console.error('Error marking paragraph as viewed:', error);
        }
    }

    scrollToParagraph(paragraphId) {
        const paragraph = document.getElementById(`paragraph-${paragraphId}`);
        if (paragraph) {
            paragraph.scrollIntoView({ behavior: 'smooth' });
        }
    }

    async updatePageNavigationButtons() {
        const currentPage = parseInt(new URLSearchParams(window.location.search).get('page')) || 1;
        
        // Fetch total pages (you'll need to add this to your API)
        const response = await fetch(`/stories/api/chapters/${this.currentChapter.id}/paragraphs/?page=${currentPage}`);
        const data = await response.json();
        
        const prevButton = document.getElementById('prevPage');
        const nextButton = document.getElementById('nextPage');

        prevButton.disabled = currentPage <= 1;
        nextButton.disabled = !data.has_next; // You'll need to add this to your API response

        // Update visual state
        prevButton.classList.toggle('opacity-50', prevButton.disabled);
        nextButton.classList.toggle('opacity-50', nextButton.disabled);
    }

    async navigateToPage(direction) {
        const currentPage = parseInt(new URLSearchParams(window.location.search).get('page')) || 1;
        const newPage = direction === 'prev' ? currentPage - 1 : currentPage + 1;
        
        if (newPage < 1) return;
        
        // Update URL and fetch new paragraphs
        this.updateUrl({
            story: this.currentStory.id,
            chapter: this.currentChapter.id,
            page: newPage
        });
        
        await this.fetchParagraphs(this.currentChapter.id, newPage);
    }

    async generateNextPage() {
        if (!this.currentChapter) {
            console.error('No chapter selected');
            return;
        }

        const currentPage = parseInt(new URLSearchParams(window.location.search).get('page')) || 1;
        const generateButton = document.getElementById('nextPage');
        
        // Update button to show loading state
        generateButton.disabled = true;
        generateButton.innerHTML = `
            <div class="flex items-center justify-center">
                <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                <span class="ml-2">Generating...</span>
            </div>
        `;

        try {
            const response = await fetch(`/stories/api/chapters/${this.currentChapter.id}/generate_next_page/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({ current_page: currentPage })
            });

            if (!response.ok) {
                throw new Error('Failed to generate next page');
            }

            // Navigate to the newly generated page
            await this.navigateToPage('next');

        } catch (error) {
            console.error('Error generating next page:', error);
            generateButton.textContent = 'Failed to generate. Try again';
            generateButton.classList.add('bg-red-600');
        } finally {
            generateButton.disabled = false;
        }
    }

    setupGenerateParagraphButton() {
        console.log('Setting up generate paragraph button...');
        const generateButton = document.getElementById('generateParagraphButton');
        if (generateButton) {
            generateButton.addEventListener('click', () => this.generateNextParagraph());
        }
    }

    async generateNextParagraph() {
        if (!this.currentChapter) {
            console.error('No chapter selected');
            return;
        }

        const generateButton = document.getElementById('generateParagraphButton');
        if (!generateButton) return;

        // Update button to show loading state
        generateButton.disabled = true;
        generateButton.innerHTML = `
            <div class="flex items-center justify-center">
                <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                <span class="ml-2">Generating...</span>
            </div>
        `;

        try {
            const currentPage = parseInt(new URLSearchParams(window.location.search).get('page')) || 1;
            const response = await fetch(`/stories/api/chapters/${this.currentChapter.id}/generate_paragraph/?page=${currentPage}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                }
            });

            if (!response.ok) {
                throw new Error('Failed to generate paragraph');
            }

            // Refresh the current page to show the new paragraph
            await this.fetchParagraphs(this.currentChapter.id, currentPage);
            generateButton.textContent = 'Generate Next Paragraph';

        } catch (error) {
            console.error('Error generating paragraph:', error);
            generateButton.textContent = 'Failed to generate. Try again';
            generateButton.classList.add('bg-red-600');
        } finally {
            generateButton.disabled = false;
        }
    }
}

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    new StoryReader();
});