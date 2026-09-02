# 🇩🇪 ANFRAGE Automation 2.0 - Web Version

Multi-user web application for automatically sending German apprenticeship (Ausbildung) inquiry emails. Transform your local CLI tool into a hosted web service that you and your friends can use.

## 🎯 What's New in Version 2.5

- **🌐 Web Interface**: User-friendly Streamlit web app
- **👥 Multi-User Support**: Multiple users with separate accounts
- **🔐 User Authentication**: Username/password login system
- **📝 Self-Registration**: Users can register themselves
- **👨‍💼 Admin Dashboard**: View all users and system statistics
- **🗄️ Database Backend**: SQLite database for better data management
- **🔄 Shared Caching**: Company data and email resolution shared across users
- **🛡️ Safety Features**: Automatic domain blocking for bounced emails
- **📊 Progress Tracking**: Real-time progress updates during email campaigns
- **💾 Automatic Backups**: Built-in database backup system
- **🌍 Remote Access**: Can be deployed for access from anywhere

## 🚀 Quick Start (Local Testing)

### Prerequisites
- Python 3.8+
- pip package manager

### Installation

1. **Navigate to the project directory:**
   ```bash
   cd "C:\Users\Yassine\Desktop\GERMANY\BEWERBUNG\AUTOMATION 2.0"
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   copy .env.example .env
   # Edit .env with your settings
   ```

5. **Initialize the database and add users:**
   ```bash
   python add_user.py
   ```

6. **Run the web application:**
   ```bash
   streamlit run app.py
   ```

7. **Open in browser:**
   ```
   http://localhost:8501
   ```

## 🌐 Production Deployment

For hosting the application on a VPS for multi-user access, follow the **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** for detailed step-by-step instructions.

### Quick Deployment Summary:
1. Get a VPS (DigitalOcean/Hetzner)
2. Set up server with required software
3. Deploy application files
4. Configure Nginx web server
5. Set up SSL certificates
6. Configure automatic backups

## 📁 Project Structure

```
AUTOMATION 2.0/
├── app.py                      # Streamlit web interface
├── core.py                     # Core business logic
├── db.py                       # Database operations
├── categories.py               # Job categories and templates
├── add_user.py                 # User management script
├── backup_db.py                # Database backup script
├── schema.sql                  # Database schema
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── DEPLOYMENT_GUIDE.md        # Detailed deployment guide
├── deploy/                    # Deployment configuration files
│   ├── anfrage.service        # Systemd service file
│   ├── nginx.conf            # Nginx configuration (HTTP)
│   └── nginx-ssl.conf        # Nginx configuration (HTTPS)
└── backups/                   # Database backups (created automatically)
```

## 🔧 Configuration

### Environment Variables (.env file)

```bash
# Database Configuration
DATABASE_PATH=anfrage.db

# Application Configuration
DELAY=5                      # Delay between emails in seconds
BOUNCE_CHECK_EVERY=20       # Check for bounces every N emails

# Security Configuration
SECRET_KEY=your_secret_key_here_for_sessions

# Hosting Configuration (for production)
DOMAIN=your-domain.com
PORT=8501
```

## 👥 User Management

### Adding Users

Run the user management script:
```bash
python add_user.py
```

You'll be prompted to enter:
- User's name
- Gmail address
- Gmail App Password (from Google Account > Security > App Passwords)

### User Selection

When you start the web application, you'll see a list of registered users and can select which account to use for the session.

## 🎨 Web Interface Features

### User Dashboard
- User login/selection
- Session history and statistics
- Real-time progress tracking

### Campaign Configuration
- Category selection (Pflege, Technik, Handwerk, Gastronomie)
- Specific profession selection
- German region/state selection
- Email count target per session

### Email Preview
- Preview the German email template
- Personalized with user's name
- Profession-specific content

### Progress Tracking
- Real-time progress bar
- Status messages for each email
- Success/failure statistics

### Results Dashboard
- Session summary (sent, failed, skipped, no email)
- Recent contact history
- Easy access to start new sessions

## 🗄️ Database Schema

The SQLite database contains the following tables:

- **users**: User accounts and credentials
- **companies**: Cached company data from Overpass API
- **resolved_emails**: Cached email resolution results
- **contacts**: Contact history and deduplication
- **blocked_domains**: Shared domain blocklist
- **jobs**: Job execution history

## 🔒 Security Features

### Per-User Isolation
- Each user has separate contact history
- Users can contact the same companies (they're different applicants)
- Gmail credentials stored securely in database

### Shared Safety
- Blocked domains affect all users (bounced emails)
- Automatic bounce detection and blocking
- Shared caching reduces API calls and scraping

### Data Protection
- SQLite database with proper indexing
- Environment variables for sensitive configuration
- Regular automated backups

## 💾 Backup System

### Manual Backup
```bash
python backup_db.py
```

### Automatic Backups
Set up a cron job for daily backups (included in deployment guide):
```bash
0 2 * * * cd /path/to/anfrage-automation && /path/to/venv/bin/python backup_db.py
```

### Backup Retention
By default, keeps the last 7 backups to save space while maintaining recent history.

## 🛠️ Troubleshooting

### Database Issues
```bash
# Check database file
ls -la anfrage.db

# Recreate database
rm anfrage.db
python add_user.py
```

### Port Already in Use
```bash
# Find process using port 8501
netstat -ano | findstr :8501  # Windows
netstat -tlnp | grep 8501     # Linux

# Kill the process or use different port
streamlit run app.py --server.port=8502
```

### Python Dependencies
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

## 📊 Performance Optimization

### Shared Caching
- Company data cached for 7 days
- Email resolution cached permanently
- Reduces Overpass API calls and website scraping

### Rate Limiting
- Configurable delay between emails (default: 5 seconds)
- Respects Gmail daily sending limits
- Automatic bounce detection

## 🚀 Next Steps

1. **Test locally** using the quick start guide
2. **Deploy to VPS** following the deployment guide
3. **Add users** (yourself and friends)
4. **Run test campaigns** with small email counts
5. **Monitor performance** and adjust settings as needed
6. **Set up monitoring** (optional) for production

## 📞 Support

For deployment issues, refer to the [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) troubleshooting section.

## 🔄 From Version 1.0 to 2.0

### Migration Notes
- Excel trackers replaced with SQLite database
- Hardcoded credentials moved to users table
- Shared caching system for better performance
- Web interface replaces CLI interaction
- Multi-user support built-in

### Data Migration
If you have existing Excel trackers from version 1.0, you can manually add the contact history to the new database, or start fresh with the improved system.

## 📝 License

This is a personal project for German apprenticeship applications. Please use responsibly and respect email sending best practices.

---

**Ready to transform your job hunting process? Deploy it today and share with your friends!** 🚀