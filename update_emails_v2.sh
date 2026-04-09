#!/bin/bash
#
# Email Update Pipeline V2
# 
# This script runs the email processing pipeline:
# 1. Extracts new emails from Gmail using OAuth2 authentication with deduplication
# 2. Creates chunks and embeddings for vector search (RAG)
# 3. Classifies emails using LLM (Gemini) and creates enhanced embeddings
# 4. Analyzes customer issues, tracks resolutions, and generates fix documentation
#
# The pipeline includes:
# - Email extraction with content deduplication 
# - Smart chunking with vector embeddings (all-MiniLM-L6-v2)
# - Multi-label classification into business pipelines
# - Enhanced embeddings with sender history and thread context
# - Customer issue tracking with resolution analysis
# - Automatic fix documentation generation
# - Vector search capability with pgvector
#
# Usage:
#   ./update_emails_v2.sh                           # Extract all new emails
#   ./update_emails_v2.sh --start-date 2024/01/01   # Extract emails from specific date
#   ./update_emails_v2.sh --max-results 100         # Limit number of emails
#   ./update_emails_v2.sh --setup                   # Run initial setup

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running setup
if [[ "$1" == "--setup" ]]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Email Pipeline Initial Setup${NC}"
    echo -e "${GREEN}========================================${NC}\n"

    # Check Python
    echo -e "${YELLOW}Checking Python installation...${NC}"
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3 is not installed${NC}"
        echo "Please install Python 3.8 or higher"
        exit 1
    fi
    python3 --version

    # Create virtual environment
    if [ ! -d "venv" ]; then
        echo -e "\n${YELLOW}Creating virtual environment...${NC}"
        python3 -m venv venv
    fi

    # Activate virtual environment
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source venv/bin/activate

    # Install dependencies
    echo -e "\n${YELLOW}Installing Python dependencies...${NC}"
    pip install --upgrade pip
    pip install -r requirements.txt

    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        echo -e "\n${YELLOW}Creating .env file from template...${NC}"
        cp .env.example .env
        echo -e "${GREEN}Created .env file. Please edit it with your configuration:${NC}"
        echo "  - Gmail authentication: Run 'python setup_oauth.py' to configure"
        echo "  - LLM_API_KEY: Your Gemini API key"
    fi

    # Create database tables (SQLite + LanceDB - no server needed)
    echo -e "\n${YELLOW}Setting up database...${NC}"
    python scripts/setup_all_tables.py

    # Download ML models
    echo -e "\n${YELLOW}Downloading ML models (this may take a few minutes)...${NC}"
    python -c "
from sentence_transformers import SentenceTransformer
print('Downloading sentence transformer model...')
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
print('Model downloaded successfully!')
"

    # Check OAuth configuration
    echo -e "\n${YELLOW}Checking Gmail OAuth configuration...${NC}"
    oauth_config="$HOME/.email-pipeline/config/oauth_config.json"
    if [ ! -f "$oauth_config" ]; then
        echo -e "${YELLOW}OAuth not configured yet. Running setup...${NC}"
        echo "Please follow the OAuth setup wizard:"
        python setup_oauth.py
        if [ $? -ne 0 ]; then
            echo -e "${RED}OAuth setup failed${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}OAuth configuration found${NC}"
    fi

    # Final instructions
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}Setup Complete!${NC}"
    echo -e "${GREEN}========================================${NC}\n"
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Edit .env file with your Gemini API key"
    echo "2. Run the pipeline: ./update_emails_v2.sh"
    echo ""
    echo -e "${BLUE}For more help, see README.md${NC}"
    exit 0
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# Check required environment variables
check_environment() {
    echo -e "${YELLOW}Checking configuration...${NC}"
    
    # Check for .env file
    if [ ! -f ".env" ]; then
        echo -e "${RED}Error: .env file not found${NC}"
        echo "Run './update_emails_v2.sh --setup' to create initial configuration"
        exit 1
    fi
    
    # Check OAuth configuration
    oauth_config="$HOME/.email-pipeline/config/oauth_config.json"
    if [ ! -f "$oauth_config" ]; then
        echo -e "${RED}Error: Gmail OAuth not configured${NC}"
        echo "Please run: python setup_oauth.py"
        exit 1
    fi
    
    if [ -z "$LLM_API_KEY" ]; then
        echo -e "${RED}Error: LLM_API_KEY not set${NC}"
        echo "Please set your Gemini API key in .env"
        exit 1
    fi
    
    echo -e "${GREEN}Configuration OK${NC}"
}

# Ensure database exists
check_database() {
    if [ ! -f "data/limrose.db" ]; then
        echo -e "${RED}Error: Database not found at data/limrose.db${NC}"
        echo "Run './update_emails_v2.sh --setup' to create the database"
        exit 1
    fi
    echo -e "${GREEN}Database found${NC}"
}

# Check environment before starting
check_environment

# Check database before starting
check_database

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Email Update Pipeline V2${NC}"
echo -e "${GREEN}========================================${NC}"

# Step 1: Extract new emails from Gmail
echo -e "\n${YELLOW}Step 1: Extracting new emails from Gmail...${NC}"
# Debug: Check if environment variables are set
echo "DEBUG: HF_HUB_OFFLINE=$HF_HUB_OFFLINE"
python gmail_oauth_extractor.py "$@"

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Gmail extraction failed!${NC}"
    exit 1
fi

# Step 2: Create chunks and embeddings from extracted emails
echo -e "\n${YELLOW}Step 2: Creating chunks and embeddings from emails...${NC}"
echo "This will chunk emails and generate embeddings for RAG search"

# Run batch processing to create email_chunks with embeddings
python batch_process_all_emails.py

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Email chunking and embedding failed!${NC}"
    exit 1
fi

# Step 3: Classify emails using LLM
echo -e "\n${YELLOW}Step 3: Classifying emails into pipelines...${NC}"
echo "Using Gemini Flash to classify emails..."
echo "Classifications include: editorial, sales, press releases, newsletters, etc."
echo "This also creates enhanced embeddings with classification context"

# Run classifier to process ALL unclassified emails in batches
python batch_llm_classifier_optimized.py --all --batch-size 50

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Email classification failed!${NC}"
    echo "Note: This step requires Gemini API key to be configured"
    exit 1
fi

# Step 4: Process customer issues (if any were classified)
echo -e "\n${YELLOW}Step 4: Analyzing customer issues...${NC}"
echo "Checking for emails classified as customer issues..."

# Check if there are any customer issue emails
CUSTOMER_ISSUES=$(python -c "
from config.database import get_connection
conn = get_connection()
cur = conn.cursor()
cur.execute('''
    SELECT COUNT(DISTINCT ce.id)
    FROM classified_emails ce
    JOIN email_pipeline_routes epr ON ce.id = epr.email_id
    WHERE epr.pipeline_type IN (\"customer_issue\", \"customer_complaint\", \"customer_service_or_feedback\")
''')
count = cur.fetchone()[0]
print(count)
conn.close()
" 2>/dev/null || echo "0")

if [ "$CUSTOMER_ISSUES" -gt 0 ]; then
    echo "Found $CUSTOMER_ISSUES customer issue emails to analyze"
    echo "Using semantic vector search for intelligent issue resolution..."
    python customer_issue_tracker_v2.py --batch-size 50
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Customer issue analysis complete (with vector similarity)${NC}"
        # Show quick stats
        python customer_issue_tracker_v2.py --stats | head -20
    else
        echo -e "${YELLOW}Warning: Customer issue tracking encountered errors${NC}"
    fi
else
    echo "No customer issue emails found in this batch"
fi

# Success
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Email pipeline completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"

# Show summary statistics
echo -e "\n${YELLOW}Pipeline Summary:${NC}"
python -c "
import sys
try:
    from config.database import get_connection

    conn = get_connection()
    cur = conn.cursor()

    cur.execute('SELECT COUNT(*) FROM classified_emails')
    total_emails = cur.fetchone()[0]

    cur.execute('''
        SELECT COUNT(*) FROM classified_emails
        WHERE created_at >= datetime(\"now\", \"-24 hours\")
    ''')
    recent_emails = cur.fetchone()[0]

    cur.execute('''
        SELECT pipeline_type, COUNT(DISTINCT email_id) as count
        FROM email_pipeline_routes
        GROUP BY pipeline_type
        ORDER BY count DESC
        LIMIT 10
    ''')
    classifications = cur.fetchall()

    cur.execute('SELECT COUNT(*) FROM classified_emails WHERE chunks_created = 1')
    emails_with_chunks = cur.fetchone()[0]

    cur.execute('SELECT COUNT(DISTINCT email_id) FROM enhanced_email_embeddings')
    emails_with_enhanced = cur.fetchone()[0]

    cur.execute('SELECT COUNT(*) FROM email_duplicate_groups WHERE member_count > 1')
    duplicate_groups = cur.fetchone()[0]

    cur.execute('SELECT COUNT(DISTINCT sender_email) FROM sender_interaction_history')
    unique_senders = cur.fetchone()[0]

    cur.execute('''
        SELECT
            COUNT(*) as total_issues,
            SUM(CASE WHEN has_resolution THEN 1 ELSE 0 END) as resolved
        FROM customer_issues_v2
    ''')
    issue_stats = cur.fetchone()
    total_issues = issue_stats[0] or 0
    resolved_issues = issue_stats[1] or 0

    print(f'Total emails processed: {total_emails:,}')
    print(f'New emails (last 24h): {recent_emails:,}')
    print(f'Duplicate email groups: {duplicate_groups:,}')

    if total_emails > 0:
        print(f'\\nEmbedding Coverage:')
        print(f'  Emails with chunks: {emails_with_chunks:,} ({emails_with_chunks/total_emails*100:.1f}%)')
        print(f'  Enhanced embeddings: {emails_with_enhanced:,} ({emails_with_enhanced/total_emails*100:.1f}%)')

    print(f'\\nClassification Breakdown:')
    if classifications:
        for row in list(classifications)[:5]:
            print(f'  {row[0]}: {row[1]:,}')
        if len(classifications) > 5:
            print(f'  ... and {len(classifications)-5} more categories')
    else:
        print('  No classifications yet')

    if unique_senders > 0:
        print(f'\\nSender Intelligence:')
        print(f'  Unique senders tracked: {unique_senders:,}')

    if total_issues > 0:
        print(f'\\nCustomer Issues:')
        print(f'  Total issues tracked: {total_issues:,}')
        print(f'  Issues resolved: {resolved_issues:,} ({resolved_issues/total_issues*100:.1f}%)')

    conn.close()

except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

echo -e "\n${GREEN}Your email processing system is ready for use!${NC}"
echo -e "${BLUE}Features:${NC}"
echo -e "  ✓ Email extraction with deduplication"
echo -e "  ✓ Vector embeddings for semantic search"
echo -e "  ✓ Multi-label classification"
echo -e "  ✓ Enhanced context embeddings"
echo -e "  ✓ Sender relationship tracking"
echo -e "  ✓ Customer issue tracking with semantic similarity"
echo -e "  ✓ Intelligent resolution suggestions"
echo -e "  ✓ Automatic fix synthesis from similar issues"