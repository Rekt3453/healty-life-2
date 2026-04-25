from django.shortcuts import render

def selector_sede(request):
   
    sedes = [
        {'nombre': 'Caracas', 'slug': 'caracas'},
        {'nombre': 'Valencia', 'slug': 'valencia'},
        {'nombre': 'Maracaibo', 'slug': 'maracaibo'},
    ]
    return render(request, 'selector.html', {'sedes': sedes})

def home_sede(request, sede_slug):
    # Esta es la página de bienvenida de cada sede
    return render(request, 'home_sede.html', {'sede': sede_slug})