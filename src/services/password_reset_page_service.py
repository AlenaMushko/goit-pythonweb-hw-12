from html import escape


def render_password_reset_page(token: str, user_id: int | None = None, message: str = "") -> str:
    safe_message = escape(message) if message else ""
    hidden_user_id = (
        f'<input type="hidden" name="user_id" value="{user_id}" />' if user_id is not None else ""
    )
    message_block = (
        f'<div style="margin-bottom:16px;padding:10px;border-radius:6px;background:#eef2ff;color:#1e3a8a;">{safe_message}</div>'
        if safe_message
        else ""
    )
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Reset Password</title>
</head>
<body style="font-family:Arial,sans-serif;background:#f5f7fb;padding:24px;">
  <div style="max-width:460px;margin:0 auto;background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:24px;">
    <h2 style="margin-top:0;">Set a new password</h2>
    {message_block}
    <form method="post" action="">
      {hidden_user_id}
      <label for="password">New password</label><br />
      <input id="password" name="password" type="password" required minlength="8" style="width:100%;padding:10px;margin-top:6px;margin-bottom:12px;" /><br />
      <label for="confirm_password">Confirm password</label><br />
      <input id="confirm_password" name="confirm_password" type="password" required minlength="8" style="width:100%;padding:10px;margin-top:6px;margin-bottom:16px;" /><br />
      <button type="submit" style="padding:10px 16px;background:#2563eb;color:#fff;border:none;border-radius:6px;cursor:pointer;">Submit</button>
    </form>
  </div>
</body>
</html>
"""
