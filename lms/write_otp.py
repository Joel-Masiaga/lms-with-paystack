content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Your Email - Kuza Ndoto Academy</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background-color: #f8fafc; }
        .otp-input { letter-spacing: 12px; font-size: 1.5rem; font-weight: 700; text-align: center; }
        .otp-input:focus { outline: none; border-color: #4f46e5; box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.2); }
    </style>
</head>
<body class="min-h-screen flex items-center justify-center p-4 bg-gray-50">
    <div class="max-w-md w-full bg-white rounded-xl shadow-lg p-8 sm:p-10 space-y-6">
        <div class="text-center">
            <div class="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-indigo-100 mb-4">
                <i class="fas fa-envelope-open-text text-2xl text-indigo-600"></i>
            </div>
            <h2 class="text-2xl sm:text-3xl font-extrabold text-gray-900">Verify Your Email</h2>
            <p class="mt-2 text-sm text-gray-600">A 6-digit code has been sent to your email.</p>
        </div>

        {% if messages %}
        <div class="mt-4">
            {% for message in messages %}
            <div class="rounded-md p-4 {% if message.tags == 'error' %}bg-red-50 text-red-800 border-red-200{% elif message.tags == 'success' %}bg-green-50 text-green-800 border-green-200{% else %}bg-blue-50 text-blue-800 border-blue-200{% endif %} border mt-2">
                <div class="flex">
                    <div class="flex-shrink-0">
                        {% if message.tags == 'error' %}<i class="fas fa-times-circle text-red-400"></i>
                        {% elif message.tags == 'success' %}<i class="fas fa-check-circle text-green-400"></i>
                        {% else %}<i class="fas fa-info-circle text-blue-400"></i>{% endif %}
                    </div>
                    <div class="ml-3"><p class="text-sm font-medium">{{ message }}</p></div>
                </div>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <form method="POST" class="mt-6 space-y-6">
            {% csrf_token %}
            <div>
                <label for="email" class="block text-sm font-medium text-gray-700">Email Address</label>
                <div class="mt-1 relative rounded-md shadow-sm">
                    <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <i class="fas fa-envelope text-gray-400"></i>
                    </div>
                    <input id="email" name="email" type="email" value="{{ email }}" required
                           class="focus:ring-indigo-500 focus:border-indigo-500 block w-full pl-10 sm:text-sm border-gray-300 rounded-md py-2.5 border"
                           placeholder="Enter your registered email">
                </div>
            </div>
            <div>
                <label for="otp" class="block text-sm font-medium text-gray-700">Verification Code</label>
                <div class="mt-1">
                    <input id="otp" name="otp" type="text" maxlength="6" pattern="\d{6}" required
                           class="appearance-none block w-full px-3 py-3 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm otp-input text-gray-800"
                           placeholder="000000" autocomplete="off">
                </div>
                <p class="mt-2 text-xs text-center text-gray-400">The verification code will expire in 10 minutes.</p>
            </div>
            <div>
                <button type="submit" class="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors">
                    <i class="fas fa-check-circle mr-2 mt-1"></i> Verify Email
                </button>
            </div>
        </form>

        <div class="mt-6">
            <div class="relative">
                <div class="absolute inset-0 flex items-center"><div class="w-full border-t border-gray-200"></div></div>
                <div class="relative flex justify-center text-sm"><span class="px-2 bg-white text-gray-500">Didn't receive the code?</span></div>
            </div>
        </div>

        <div class="mt-6 flex flex-col space-y-4">
            <a href="{% url 'resend_verification' %}" class="w-full flex justify-center py-2.5 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors">
                <i class="fas fa-redo mr-2 mt-1 -ml-1 text-gray-400"></i> Request New Code
            </a>
            <a href="{% url 'register' %}" class="text-center text-sm text-gray-500 hover:text-gray-900 transition-colors mt-2 block">
                &larr; Back to Registration
            </a>
        </div>
    </div>
    <script>
        document.getElementById('otp').addEventListener('input', function(e) {
            e.target.value = e.target.value.replace(/\D/g, '').slice(0, 6);
        });
    </script>
</body>
</html>'''
with open('users/templates/users/verify_email_pending.html', 'w', encoding='utf-8') as f:
    f.write(content)
