from django.contrib import admin


class ProjectAdmin(admin.AdminSite):
    site_title = "Administración de Proyecto"
    site_header = "Proyecto"
    index_title = "Lista de Mantenimientos"
    site_url = "/"


project_admin = ProjectAdmin(name="project_admin")
