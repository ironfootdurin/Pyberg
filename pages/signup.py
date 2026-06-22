from nicegui import ui, app
import user

class SignUpPage:
    def __init__(self):
        with ui.column().classes('w-full mt-2 h-screen items-center justify-center p-4'):
            with ui.card().classes('max-w-md bg-secondary p-8 rounded-2xl shadow-xl gap-2 border-dark/20'):
                ui.label('Create an account:').classes('text-2xl text-primary')
                self.username_input = ui.input(label = 'Username').classes('w-full').props('autocomplete=off')
                self.password_input = ui.input(label = 'Password', password=True).classes('w-full').props('autocomplete=off')

                ui.button('Create account', on_click=self.handle_signup).classes('w-full bg-info text-white py-2') 
                ui.link('Already have an account? Sign in', '/').classes('''w-full text-center text-sm pt-2
                                                                    text-gray-400 hover:text-accent transition-colors mt-1''')
                self.password_input.on('keydown.enter', self.handle_signup)


    def handle_signup(self):
        user_val = self.username_input.value.strip()
        pass_val = self.password_input.value
        if not user_val or not pass_val:
            ui.notify('Please fill in bothe a username and a password.', type='warning')
            return
        success = user.create(user_val, pass_val)
        if success:
            ui.notify('Account created successfully.', type='positive')
            app.storage.user['username'] = user_val
            ui.navigate.to('/home')
        else:
            ui.notify('Username taken.', type='negative')
            return
                
