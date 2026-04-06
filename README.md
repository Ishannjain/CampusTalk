# CampusConnect

A Django-based social platform for campus communities, featuring user authentication, posts with comments, common chat, and private messaging.

## Features

### Authentication
- User registration and login
- JWT token-based authentication with secure cookie storage
- Session management

### Posts & Comments
- Create common posts visible to all users
- Add comments to posts
- Real-time display of posts and comments on the home page

### Chat System
- **Common Chat**: Shared chat room for all users
- **Personal Chat**: Private messaging between individual users
- Chat previews on the home page

### User Interface
- Responsive Bootstrap-based design
- Navigation bar with links to home, profile, and chat
- User-friendly forms for posts, comments, and messages

## Technologies Used

- **Backend**: Django 6.0.2
- **Database**: SQLite3
- **Frontend**: HTML, CSS, Bootstrap 4.4.1
- **Authentication**: JWT (JSON Web Tokens) via PyJWT
- **Python**: 3.14.0

## Installation

1. **Clone or download the project**:
   ```
   cd "c:\Users\G\Desktop\3rd Year\Sem-6\SE lab\campusconnect"
   ```

2. **Install dependencies**:
   ```
   pip install -r requirements.txt
   ```
   Or manually:
   ```
   pip install Django==6.0.2 PyJWT==2.8.0
   ```

3. **Run migrations**:
   ```
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Create a superuser** (optional, for admin access):
   ```
   python manage.py createsuperuser
   ```

5. **Run the development server**:
   ```
   python manage.py runserver
   ```

6. **Access the application**:
   - Open your browser and go to `http://127.0.0.1:8000/`

## Usage

### For New Users
1. Visit the home page and click "Create Account" to register.
2. After registration, you'll be logged in automatically.
3. Start creating posts, commenting, or chatting.

### For Existing Users
1. Click "Sign In" to log in with your credentials.
2. Once logged in, you can:
   - Create posts on the home page
   - Comment on existing posts
   - Access the common chat
   - Start personal chats with other users

### Navigation
- **Home**: View posts, create new posts, see chat previews
- **Common Chat**: Participate in community-wide chat
- **Personal Chat**: Click on usernames to start private conversations
- **Profile**: View your account information
- **Logout**: End your session

## Project Structure

```
campusconnect/
├── accounts/
│   ├── models.py          # User, CommonPost, Comment, ChatMessage models
│   ├── views.py           # View functions for authentication and features
│   ├── forms.py           # Django forms for posts, comments, chats
│   ├── urls.py            # URL patterns for the app
│   ├── admin.py           # Admin panel registration
│   ├── templates/
│   │   └── accounts/      # HTML templates
│   └── migrations/        # Database migrations
├── campusconnect/
│   ├── settings.py        # Django settings
│   ├── urls.py            # Main URL configuration
│   ├── wsgi.py            # WSGI configuration
│   └── asgi.py            # ASGI configuration
├── db.sqlite3             # SQLite database
├── manage.py              # Django management script
└── README.md              # This file
```

## API Endpoints

- `/` - Home page
- `/register/` - User registration
- `/login/` - User login
- `/logout/` - User logout
- `/profile/` - User profile
- `/create-post/` - Create a new post
- `/comment/<post_id>/` - Add comment to a post
- `/common-chat/` - Common chat page
- `/chat/<username>/` - Personal chat with a user

## Security Features

- JWT tokens for authentication
- HttpOnly cookies for token storage
- CSRF protection on forms
- User session management

## Future Enhancements

- Real-time chat using WebSockets
- File uploads for posts
- User profiles with avatars
- Notification system
- Mobile app development

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open-source and available under the MIT License.

## Contact

For questions or support, please contact the development team.