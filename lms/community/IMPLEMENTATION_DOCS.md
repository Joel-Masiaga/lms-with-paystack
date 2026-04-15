# Community Messaging System - Implementation Documentation

## Project Overview

This document describes the complete implementation of the Community Messaging System for Kuza Ndoto Academy's LMS platform. The system enables internal communication between users through direct messages, group discussions, and instructor course broadcasts.

## Architecture

### Design Pattern
The system follows Django's Model-View-Template (MVT) pattern with:
- **Models**: ORM-based data structure with relationships
- **Views**: Class-based views with permission mixing
- **Forms**: Django forms with Tailwind CSS styling
- **Templates**: Responsive HTML templates

### Key Design Decisions

1. **M2M with Through Model**: `CommunityGroup` uses `members` M2M through `GroupMember` to track roles (admin/member)
2. **Conversation Bridge**: Two-user conversations stored in separate `Conversation` model for cleaner threading
3. **Read Tracking**: `DirectMessage.is_read` field tracks message read status
4. **Role-Based Access**: `GroupMember.role` field enables admin capabilities
5. **Course Filtering**: Broadcasts filtered to instructor's own courses in form initialization

## Database Schema

### Models

```
DirectMessage
├── sender (FK → User)
├── recipient (FK → User)
├── content (TextField)
├── created_at (DateTime, auto_now_add)
├── is_read (Boolean, default=False)
└── Indexes: (sender, recipient, -created_at), (recipient, is_read)

Conversation
├── participants (M2M → User)
├── last_message_at (DateTime, auto_now=True)
└── Meta: order_by('-last_message_at')

CommunityGroup
├── name (CharField, max_length=200)
├── description (TextField)
├── creator (FK → User)
├── members (M2M → User through GroupMember)
├── is_public (Boolean)
└── created_at (DateTime, auto_now_add)

GroupMember
├── user (FK → User)
├── group (FK → CommunityGroup)
├── role (CharField: 'admin' or 'member')
├── joined_at (DateTime, auto_now_add)
└── UniqueConstraint: (user, group)

GroupMessage
├── group (FK → CommunityGroup)
├── sender (FK → User)
├── content (TextField)
├── created_at (DateTime, auto_now_add)
└── Index: (group, -created_at)

CourseBroadcast
├── course (FK → Course)
├── instructor (FK → User)
├── subject (CharField)
├── content (TextField)
├── created_at (DateTime, auto_now_add)
└── Index: (course, -created_at)
```

## URL Structure

```
/community/
├── messages/                      [ConversationListView]
├── messages/<user_id>/            [ConversationDetailView]
├── groups/                        [GroupListView]
├── groups/create/                 [CreateGroupView]
├── groups/<group_id>/             [GroupDetailView]
├── groups/<group_id>/join/        [JoinGroupView - POST]
├── groups/<group_id>/leave/       [LeaveGroupView - POST]
├── broadcast/                     [CourseBroadcastView]
└── broadcast/<course_id>/         [CourseBroadcastListView]
```

## Views Specification

### ConversationListView
- **URL**: `/community/messages/`
- **Method**: GET
- **Auth**: LoginRequired
- **Context**: 
  - `conversations`: Sorted by last_message_at
- **Displays**: All conversations for authenticated user

### ConversationDetailView
- **URL**: `/community/messages/<user_id>/`
- **Method**: GET, POST
- **Auth**: LoginRequired
- **POST Handler**: Creates DirectMessage, marks as read
- **Context**:
  - `messages`: Messages between users
  - `form`: DirectMessageForm
  - `other_user`: User object
- **Features**:
  - Auto-creates Conversation if not exists
  - Sets is_read=False for new messages
  - Supports messaging oneself

### GroupListView
- **URL**: `/community/groups/`
- **Method**: GET
- **Auth**: LoginRequired (conditional rendering for non-auth)
- **Context**:
  - `user_groups`: Groups user is member of
  - `available_groups`: Public groups user hasn't joined
- **Features**: Distinguishes joined vs available groups

### GroupDetailView
- **URL**: `/community/groups/<group_id>/`
- **Method**: GET, POST
- **Auth**: Conditional (can view if member or group is public)
- **POST Handler**: Add message if member
- **Context**:
  - `messages`: Group messages
  - `group`: Group object
  - `is_member`: Boolean
  - `is_admin`: Boolean
  - `form`: GroupMessageForm
- **Features**: Member-only message posting

### CreateGroupView
- **URL**: `/community/groups/create/`
- **Method**: GET, POST
- **Auth**: LoginRequired
- **POST Handler**: 
  - Creates group
  - Adds creator as admin member
  - Redirects to group_detail
- **Form**: CreateGroupForm

### JoinGroupView
- **URL**: `/community/groups/<group_id>/join/`
- **Method**: POST
- **Auth**: LoginRequired
- **Handler**: Adds user to group as member
- **Redirect**: Back to group_detail

### LeaveGroupView
- **URL**: `/community/groups/<group_id>/leave/`
- **Method**: POST
- **Auth**: LoginRequired
- **Handler**: Removes user from group

### CourseBroadcastView
- **URL**: `/community/broadcast/`
- **Method**: GET, POST
- **Auth**: LoginRequired + UserPassesTest (instructor only)
- **POST Handler**:
  - Creates CourseBroadcast
  - Verifies course ownership
  - Redirects to broadcast_list
- **Form**: CourseBroadcastForm
- **Special**: Form filters courses to user's courses

### CourseBroadcastListView
- **URL**: `/community/broadcast/<course_id>/`
- **Method**: GET
- **Auth**: LoginRequired
- **Access**: Instructor or enrolled student only
- **Context**:
  - `broadcasts`: Course broadcasts ordered by -created_at
  - `course`: Course object
  - `is_instructor`: Boolean

## Forms

### DirectMessageForm
```python
Fields:
- content (Textarea, required)
  ├── Widget: Textarea
  ├── Attrs: rows=3, Tailwind classes
  └── Required: True
```

### CreateGroupForm
```python
Fields:
- name (CharField, max_length=200, required)
- description (CharField, widget=Textarea, required)
- is_public (BooleanField, required, initial=True)
```

### GroupMessageForm
```python
Fields:
- content (Textarea, required)
```

### CourseBroadcastForm
```python
Fields:
- course (ModelChoiceField, queryset filtered to user's courses)
- subject (CharField, required)
- content (CharField, widget=Textarea, required)

Special Handling:
- __init__ receives user, filters courses to user.courses_created.all()
```

## Templates

### conversation_list.html
- Lists all open conversations
- Shows last message timestamp
- User profile pictures
- "View Chat" buttons
- Empty state guidance

### conversation_detail.html
- Message thread between two users
- Auto-scroll to bottom
- Send message form
- User profile header
- Timestamp on each message

### group_list.html
- Tabbed view: Your Groups | Public Groups
- Shows member count
- Privacy indicator (Public/Private)
- "Join Group" buttons for public
- "View Group" buttons for joined
- "Create Group" button in header

### group_detail.html
- Group name and description
- Members list (sidebar)
- Message thread
- Send message form (member-only)
- Leave/Join buttons
- Privacy indicator

### create_group.html
- Group name input
- Description textarea
- Public/Private radio buttons
- Create/Cancel buttons
- Tips section

### course_broadcast.html
- Course selector dropdown (instructor's courses)
- Subject input
- Content textarea
- Send Broadcast button
- guidelines box

### course_broadcast_list.html
- List of all broadcasts for course
- Sender name and timestamp
- Broadcast subject and content
- Instructor-only "New Broadcast" button
- Empty state for courses without broadcasts

## Form Styling

All forms use Tailwind CSS with consistent theme:
```
Textareas/Inputs:
├── px-4 py-2
├── border border-gray-300 dark:border-gray-600
├── rounded-lg
├── dark:bg-gray-700 dark:text-white
└── focus:ring-2 focus:ring-primary

Submit Buttons:
├── bg-primary text-white
├── hover:bg-primary-dark
└── transition
```

## Admin Interface

### DirectMessageAdmin
- List display: sender, recipient, created_at, is_read
- Filters: is_read, created_at
- Search: sender, recipient, content

### ConversationAdmin
- List display: id, created_at, last_message_at
- Filter horizontal: participants
- Readonly: created_at, last_message_at

### CommunityGroupAdmin
- List display: name, creator, is_public, created_at
- Search: name, description
- Filter: is_public, created_at
- Filter horizontal: members

### GroupMemberAdmin
- List display: user, group, role, joined_at
- Filters: role, joined_at
- Search: user, group

### GroupMessageAdmin
- List display: sender, group, created_at
- Search: sender__username, group__name, content
- Filter: created_at

### CourseBroadcastAdmin
- List display: course, instructor, subject, created_at
- Search: course__title, instructor__username, subject, content
- Filter: created_at

## Permission Model

| Action | Requirements |
|--------|--------------|
| View Conversations | LoginRequired |
| Send Message | LoginRequired + Recipient exists |
| View Groups | LoginRequired (public groups visible to all) |
| Join Public Group | LoginRequired + Group.is_public=True |
| Leave Group | LoginRequired + IsMember |
| View Group Details | LoginRequired + (IsMember OR Group.is_public) |
| Post to Group | LoginRequired + IsMember |
| Create Group | LoginRequired |
| Broadcast | LoginRequired + IsInstructor + CourseOwnership |
| View Broadcasts | LoginRequired + (IsInstructor OR IsEnrolled) |

## Integration Points

### Sidebar Navigation
- Added in `home/base.html`
- Both desktop (`l1-sidebar`) and mobile (`l1-mobile-sidebar`)
- Active state tracking for current page
- Conditional instructor-only "Broadcast" link

### Django Settings
- Added `'community'` to INSTALLED_APPS
- Email configuration for future notifications

### Main URL Configuration
- Added `path('community/', include('community.urls'))` to main urls.py

## Testing Checklist

- [x] Models can be imported and queried
- [x] Migrations created and applied successfully
- [x] Views and URLs configured
- [x] Forms validate correctly
- [x] Admin interface accessible
- [x] System check passes
- [ ] Direct messaging functional end-to-end
- [ ] Group creation and member management working
- [ ] Instructor broadcasts functioning
- [ ] Navigation links active and styled
- [ ] Responsive design on mobile
- [ ] Permission checks enforced

## Deployment Notes

### Required Settings
```python
INSTALLED_APPS = [
    ...
    'community',
    ...
]

TEMPLATES = [...] # Uses default engine
```

### Database Migration
```bash
python manage.py makemigrations community
python manage.py migrate community
```

### Static Files
- Uses existing Tailwind CSS from CDN
- FontAwesome icons via CDN
- No custom CSS files required

### Environment Variables
None required for community system (optional for future email notifications)

## Future Enhancements

1. **Real-time Messaging** with WebSockets/Channels
2. **Message Search** across conversations and groups
3. **File Sharing** in messages
4. **Typing Indicators** for better UX
5. **Message Reactions** (emoji responses)
6. **Group Invitations** instead of public joining
7. **Notification System** with email/push
8. **Unread Badge** count on sidebar
9. **Message Editing/Deletion** with timestamps
10. **Voice Messages** integration

## Support and Troubleshooting

### Common Issues

**Q: Migration failed**
A: Ensure community app is in INSTALLED_APPS before running migrations

**Q: Views return 404**
A: Check URL routing in main urls.py includes community URLs

**Q: Permission denied errors**
A: Verify LoginRequired on views and instructor checks on broadcast

**Q: Forms not rendering**
A: Check template includes {% csrf_token %} and form field rendering

## File Structure

```
community/
├── __init__.py
├── admin.py              [6 model admins]
├── apps.py              [CommunityConfig]
├── models.py            [6 models with indexes]
├── forms.py             [4 forms with styling]
├── views.py             [9 view classes]
├── urls.py              [9 URL patterns]
├── migrations/
│   ├── __init__.py
│   └── 0001_initial.py [Generated migration]
├── templates/community/
│   ├── conversation_list.html
│   ├── conversation_detail.html
│   ├── group_list.html
│   ├── group_detail.html
│   ├── create_group.html
│   ├── course_broadcast.html
│   └── course_broadcast_list.html
└── USER_GUIDE.md        [User documentation]
```

---

**Status**: ✅ Complete and Ready for Testing
**Version**: 1.0
**Last Updated**: {{ date }}
