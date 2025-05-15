from django.shortcuts import render, redirect
import pyrebase
import requests #註冊
import datetime #註冊


config = {
  "apiKey": "AIzaSyDvcDRm9y7yGBKgtTTAR1TTUz09RhVBEX8",
  "authDomain": "jango-login.firebaseapp.com",
  "projectId": "jango-login",
  "storageBucket": "jango-login.firebasestorage.app",
  "messagingSenderId": "708803766650",
  "appId": "1:708803766650:web:da3e8effc0b6c200f34ec3",
  "databaseURL": "https://jango-login-default-rtdb.firebaseio.com/",
}

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database() #註冊


def home(request):
    if 'firebase_user_id' in request.session:  # 2. 檢查 session 是否有 'firebase_user_id' (登入邏輯設定的)
        context = {
            'user_email': request.session.get('firebase_email', '用戶'),  # 從 session 獲取 email
            'firebase_user_id': request.session.get('firebase_user_id')   # 從 session 獲取 user_id
        }
        return render(request, 'polls/home.html', context)  # 3. 顯示頁面，同時帶出 user 資料
    else:
        return redirect('/login')  # 1. 改成沒登入，就強制到 /login 頁面


def login(request):
    return render(request, "polls/login.html")

def verify_login(request):
    account = request.POST.get('account', '')
    password = request.POST.get('password', '')
    ischecked = request.POST.get('ischecked', '')
    print('***', account, password, ischecked)
    try:
        user = auth.sign_in_with_email_and_password(account, password)
        print('user', user)
         # 登入成功，將 Firebase 用戶資訊存入 Django session
        request.session['firebase_user_id'] = user['localId']
        request.session['firebase_email'] = user.get('email', account)
        request.session.modified = True
        # 登入成功後重定向到首頁
        return redirect('/')
    except:
        print('*** login failed')
        return render(request, "polls/login.html", {'error': 'Login failed. Please check your credentials.'})

def logout(request):
    # 清除與 Firebase 登入相關的 Django session 資訊
    keys_to_delete = ['firebase_user_id', 'firebase_email']
    for key in keys_to_delete:
        if key in request.session:
            del request.session[key]

    print("用戶已登出，相關 session 已清除。")
    # 重定向到登入頁面
    return redirect('/login')

   
def register(request):
    return render(request, "polls/register.html")

def verify_register(request):
    email = request.POST.get('email', '')
    username = request.POST.get('username', '')
    password = request.POST.get('password', '')
    ischecked = request.POST.get('ischecked', '')
    print('***', email, username, password, ischecked)
   
    try:
        # 檢查使用者名稱是否已在 Realtime Database 中存在 (應用程式層級的唯一性檢查)
        username_node = db.child("usernames").child(username).get()
        if username_node.val() is not None:
            error_message = f"使用者名稱 '{username}' 已經被使用，請選擇其他名稱。"
            print(f"*** 使用者名稱 '{username}' 已存在於 Realtime Database。")
            return render(request, "polls/register.html", {'error': 'Username or email already exist.'})
        else:
            new_user_auth = auth.create_user_with_email_and_password(email, password)
            uid = new_user_auth.get('localId')
            id_token = new_user_auth.get('idToken')

            print(f"*** Firebase Auth 使用者建立成功: UID='{uid}', Email='{email}'")

            user_profile_data = {
                "username": username,
                "email": email,
                "created_at": datetime.datetime.now().isoformat() + "Z"
            }
            
            # 儲存到 /users/<uid>/ (儲存使用者詳細資料)
            # 確保您的 Realtime Database 安全規則允許已驗證使用者寫入他們自己的 UID 路徑
            # 例如: "/users/$uid/.write": "$uid === auth.uid"
            db.child("users").child(uid).set(user_profile_data, token=id_token)
            return render(request, "polls/login.html")
    except:
        print('*** register failed')
        return render(request, "polls/register.html", {'error': 'Register failed. Please check your credentials.'})
   
