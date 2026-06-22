from nicegui import ui, app
import user

class LoginPage:
    def __init__(self):
        with ui.column().classes('w-full mt-2 h-screen items-center justify-center p-4'):
            with ui.card().classes('max-w-md bg-secondary p-8 rounded-2xl shadow-xl gap-2 border-dark/20'):
                ui.label('Welcome to Pyberg!').classes('text-2xl text-primary')
                self.username_input = ui.input(label = 'Username').classes('w-full')
                self.password_input = ui.input(label = 'Password', password=True).classes('w-full')

                ui.button('Sign In', on_click=self.handle_login).classes('bg-info w-full text-white py-2')
                ui.link("Don't have an account? Sign up", '/signup').classes('''w-full text-center text-sm
                                                                                    pt-2 text-gray-400 hover:text-accent transition-colors mt-1''')

                self.password_input.on('keydown.enter', self.handle_login)

    

    def handle_login(self):
        user_val = self.username_input.value.strip()
        pass_val = self.password_input.value
        result = user.login(user_val, pass_val)
        if result:
            ui.notify(f'Welcome {user_val}!', type = 'positive')
            app.storage.user['username'] = user_val
            ui.navigate.to('/home')
        else:
            ui.notify('Incorrect username or password', type = 'negative')

            
