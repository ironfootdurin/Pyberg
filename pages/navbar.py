from nicegui import app, ui
import find
import asyncio

class NavBar:
    def __init__(self):

        with ui.header().classes('w-full bg-secondary h-10 flex items-stretch p-0 px-2 border-b border-primary overflow-hidden gap-2'):
            with ui.link('', '/home').classes('h-full px-1 flex no-underline items-center justify-center'):
                ui.icon('home').classes('text-[24px]')
            with ui.link('', '/research').classes('h-full px-1 flex no-underline items-center justify-center overflow-hidden'): 
                ui.icon('trending_up').classes('text-[24px]')
            with ui.element('div').classes('h-full max-h-full flex px-1 cursor-pointer items-center justify-center')\
                    .on('click', self.render_search):
                ui.icon('search').classes('text-[24px] text-primary')
                
            self.ticker_input = ui.input(label = None, on_change=lambda e: self.company_finder_results(e.value)).props('dense borderless bg-gray-800 ml-2')\
                                .on('blur', self.close_search)
            ui.space()
            #with ui.link('', '/user').classes('h-full flex px-1 no-underline items-center justify-center'): 
            #   ui.icon('person').classes('text-[24px]')
                
            def handle_logout():
                app.storage.user.pop('username')
                ui.navigate.to('/')
            ui.button(icon='logout', on_click=handle_logout).props('flat').classes('h-full px-4')

        with ui.dialog().props('persistent seamless position="top"') as self.my_dialog:  
            with ui.card().classes('bg-secondary').style('margin-top: 40px'):
                self.results_container = ui.column()
                
        self.ticker_input.set_visibility(False)

    def render_search(self):
        self.ticker_input.set_visibility(True)
        self.ticker_input.run_method('focus')

    async def close_search(self):
        await asyncio.sleep(0.2)
         # self.ticker_input.set_visibility(False)
         # self.my_dialog.close()
        
    def company_finder_results(self, query):
        self.results_container.clear()
        if query:
            results = find.find(query)
            self.my_dialog.open()

            if results:
                for comp in results:
                    name = find.name(comp)
                    sector = find.sector(comp)
                    if not name or not name[0] or not sector or not sector[0]:
                        continue
                    with self.results_container:
                        with ui.row().classes('justify-between flex w-full bg-secondary border border-accent p-2 cursor-pointer')\
                        .on('click', lambda c=comp: ui.navigate.to(f'/company/{c}')):
                            with ui.column().classes('gap-1 p-2'):
                                ui.label(name[0].title()).classes('text-lg text-primary')
                                ui.label(comp).classes('text-sm text-primary')
   
                            ui.label(sector[0].title() if sector else 'Unknown').classes('text-primary')
                            self.ticker_input.run_method('focus')
