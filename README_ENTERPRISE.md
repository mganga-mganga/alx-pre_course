# 🏈 ScoutAI Enterprise - AFL Scouting Intelligence System

## 🎯 Overview

**ScoutAI Enterprise** is a comprehensive, enterprise-grade AFL scouting platform that combines advanced analytics, machine learning, and large language models to provide unprecedented insights into Australian Football League performance data.

### ✨ Key Features

- **🔐 Enterprise Authentication**: Role-based access control (Admin, Analyst, Scout, Viewer)
- **🤖 AI-Powered Analysis**: ML models for player evaluation and LLM-generated insights
- **📊 Advanced Analytics**: Comprehensive player and team performance analysis
- **📋 Professional Reporting**: PDF, Excel, and Word report generation
- **🏟️ Multi-League Support**: AFLM, AFLW, VFL, SANFL, and lower leagues
- **💬 Natural Language Chat**: AI assistant for data queries
- **🎨 Modern Interface**: Beautiful, responsive Streamlit dashboard

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd scout-ai-enterprise
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements_enterprise.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Set up PostgreSQL database**
   ```bash
   # Create database
   createdb scout_ai_afl
   
   # Create user
   psql -c "CREATE USER scout_ai WITH PASSWORD 'scout_ai_password';"
   psql -c "GRANT ALL PRIVILEGES ON DATABASE scout_ai_afl TO scout_ai;"
   ```

5. **Start the system**
   ```bash
   # Start backend API
   python -m app.main
   
   # Start dashboard (in another terminal)
   streamlit run scout_ai_enterprise_dashboard.py
   ```

6. **Access the system**
   - Dashboard: http://localhost:8501
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## 📖 User Guide

### 🔐 Authentication

The system uses JWT-based authentication with role-based access control:

- **Admin**: Full system access, user management, data operations
- **Analyst**: Data analysis, ML models, LLM access, reporting
- **Scout**: Player/team analysis, reports, basic LLM access
- **Viewer**: Read-only access to players and teams

Default admin credentials are auto-generated on first startup.

### 👤 Player Analysis

1. **Search Players**: Use the search functionality to find specific players
2. **View Performance**: Analyze career statistics and trends
3. **AI Analysis**: Generate ML predictions and LLM insights
4. **Generate Reports**: Create professional scouting reports

### 🏟️ Team Analysis

1. **Select Team**: Choose from active AFL teams
2. **Season Analysis**: Analyze performance by season
3. **Form Trends**: View recent form and performance patterns
4. **Strategic Insights**: Get AI-powered recommendations

### 📊 Advanced Analytics

- **League Overview**: Season standings and performance metrics
- **Player Comparisons**: Side-by-side statistical analysis
- **Draft Analysis**: Young player development tracking

### 📋 Reports

Generate professional reports in multiple formats:
- **PDF**: Formatted scouting reports with charts
- **Excel**: Detailed spreadsheets with data analysis
- **Word**: Professional documents for sharing

## 🛠️ Technical Architecture

### Backend (FastAPI)

```
app/
├── main.py              # FastAPI application
├── config.py            # Configuration management
├── database.py          # PostgreSQL integration
├── auth/               # Authentication services
├── services/           # Business logic
├── models/             # ML models
└── reports/            # Report generation
```

### Frontend (Streamlit)

- **scout_ai_enterprise_dashboard.py**: Main dashboard interface
- **Role-based navigation**: Dynamic UI based on user permissions
- **Interactive visualizations**: Plotly charts and graphs

### Database Schema

- **players**: Player personal information
- **player_performance**: Detailed match statistics
- **matches**: Game results and scores
- **teams**: Team information and classifications
- **users**: Authentication and authorization
- **player_analysis**: Cached AI analysis results

## 🔧 Configuration

### Environment Variables

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=scout_ai_afl
DB_USER=scout_ai
DB_PASSWORD=scout_ai_password

# LLM Integration
OPENAI_API_KEY=your-api-key
LLM_MODEL=gpt-4

# Security
SECRET_KEY=your-secret-key

# Data Source
AFL_DATA_PATH=data/afl_data_source
```

### Database Setup

The system automatically creates all necessary tables on startup. For production deployments:

1. Set up PostgreSQL with appropriate security
2. Configure connection pooling
3. Set up regular backups
4. Monitor performance

## 🤖 AI Features

### Machine Learning Models

- **Player Evaluation**: Impact scoring and potential prediction
- **Career Trajectory**: Age-based performance modeling
- **Injury Risk Assessment**: Games played pattern analysis
- **Team Performance**: Win probability and form analysis

### LLM Integration

- **Player Analysis**: Natural language scouting reports
- **Team Insights**: Strategic recommendations
- **Chat Interface**: Conversational data queries
- **Draft Recommendations**: Prospect evaluation

## 📊 Data Sources

### Primary Dataset
- **Repository**: https://github.com/akareen/AFL-Data-Analysis
- **Coverage**: 1897-2025 AFL data
- **Players**: 5,700+ comprehensive profiles
- **Matches**: 15,000+ detailed game records

### Data Processing
- **Automated Ingestion**: Background data processing
- **Quality Validation**: Data cleaning and normalization
- **Regular Updates**: Configurable refresh schedules

## 🚀 Deployment

### Development
```bash
# Install dependencies
pip install -r requirements_enterprise.txt

# Start development servers
python -m app.main &
streamlit run scout_ai_enterprise_dashboard.py
```

### Production

1. **Docker Deployment**
   ```bash
   # Build image
   docker build -t scout-ai-enterprise .
   
   # Run with Docker Compose
   docker-compose up -d
   ```

2. **Cloud Deployment**
   - Configure PostgreSQL (AWS RDS, Google Cloud SQL)
   - Set up container orchestration (Kubernetes, ECS)
   - Configure load balancing and SSL
   - Set up monitoring and logging

### Environment Setup

1. **PostgreSQL Production Config**
   ```sql
   -- Create production database
   CREATE DATABASE scout_ai_afl_prod;
   CREATE USER scout_ai_prod WITH PASSWORD 'secure-password';
   GRANT ALL PRIVILEGES ON DATABASE scout_ai_afl_prod TO scout_ai_prod;
   ```

2. **Security Configuration**
   - Use strong SECRET_KEY
   - Configure CORS properly
   - Set up HTTPS
   - Regular security updates

## 🔒 Security

### Authentication
- JWT token-based authentication
- Role-based access control
- Password hashing with bcrypt
- Token expiration and refresh

### Data Protection
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF protection

### Best Practices
- Regular security audits
- Dependency updates
- Access logging
- Rate limiting

## 📈 Performance

### Optimization
- Database indexing
- Query optimization
- Caching strategies
- Async processing

### Monitoring
- Health check endpoints
- Performance metrics
- Error tracking
- User activity logging

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Development Standards
- PEP 8 code style
- Type hints
- Comprehensive testing
- Documentation updates

## 📝 API Documentation

### Authentication Endpoints
- `POST /auth/login` - User login
- `POST /auth/register` - User registration (admin only)
- `GET /auth/users` - List users (admin only)

### Player Endpoints
- `GET /players` - List players with search
- `GET /players/{id}` - Get player details
- `POST /players/{id}/analysis` - Generate AI analysis

### Team Endpoints
- `GET /teams` - List teams
- `POST /teams/{name}/analysis` - Generate team analysis

### Report Endpoints
- `POST /reports/player/{id}` - Generate player report
- `POST /reports/team/{name}` - Generate team report
- `GET /reports/download/{filename}` - Download report

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check PostgreSQL is running
   - Verify connection parameters
   - Check firewall settings

2. **LLM Analysis Not Working**
   - Verify OpenAI API key
   - Check API quota and billing
   - Review error logs

3. **Dashboard Not Loading**
   - Check if all dependencies installed
   - Verify Python path includes app directory
   - Review Streamlit logs

### Support
- Check logs in `/var/log/scout-ai/`
- Review GitHub issues
- Contact support team

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- AFL Data Analysis repository by akareen
- Streamlit team for the amazing framework
- OpenAI for GPT-4 integration
- The AFL community for inspiration

---

**ScoutAI Enterprise** - Revolutionizing AFL scouting with AI-powered intelligence.

For support and inquiries, please contact the development team.