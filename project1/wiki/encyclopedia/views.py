import random
import re
from django import forms
from django.http import Http404
from django.shortcuts import redirect, render
import markdown

from . import util

class NewWikiForm(forms.Form):
    title = forms.CharField(label="", widget=forms.TextInput(attrs={'placeholder': 'Title'}))
    content = forms.CharField(label="", widget=forms.Textarea(attrs={'placeholder': 'Content'}))

class EditWikiForm(forms.Form):
    content = forms.CharField(label="", widget=forms.Textarea(attrs={'placeholder': 'Content'}))

def index(request):
    q = request.GET.get('q')
    if (q):
        entries = util.list_entries()

        return render(request, "encyclopedia/search.html", {
            "q": q,
            "entries": [entry for entry in entries if q.lower() in entry.lower()]
        })

    return render(request, "encyclopedia/index.html", {
        "entries": util.list_entries()
    })

def dynamic_wiki(request, title):
    entry = util.get_entry(title)
    
    if (entry):
        content = markdown.markdown(util.get_entry(title))
        
        return render(request, 'encyclopedia/wiki.html', {
            "title": title,
            "content": content
        })
    
    entries = util.list_entries()
    
    return render(request, "encyclopedia/wiki_not_found.html", {
        "q": title,
        "entries": [entry for entry in entries if title.lower() in entry.lower()]
    })

def add(request):
    if (request.method == "GET"):
        return render(request, "encyclopedia/add.html", {
            "form": NewWikiForm()
        })
    elif (request.method == "POST"):
        form = NewWikiForm(request.POST)
        if form.is_valid():
            form_data = form.cleaned_data
            util.save_entry(form_data["title"], form_data["content"])
            return redirect('encyclopedia:index')
        
        return render(request, "encyclopedia/add.html", {
            "form": form
        })
    
def random_wiki(request):
    return redirect('encyclopedia:wiki', title=random.choice(util.list_entries()))

def edit(request, title):
    data = util.get_entry(title).split('\n', 1)
    content = data[1].strip()
    title = re.search(r'^#\s*(.+)$', data[0]).group(1).strip()

    if (request.method == "GET"):
        form = EditWikiForm({
            "content": content,
        })

        return render(request, "encyclopedia/edit.html", {
            "title": title,
            "form": form,
        })
    elif (request.method == "POST"):
        form = EditWikiForm(request.POST)
        if form.is_valid():
            form_data = form.cleaned_data
            util.save_entry(title, form_data["content"])
            return redirect('encyclopedia:wiki', title=title)
        
        return render(request, "encyclopedia/edit.html", {
            "title": title,
            "form": form,
        })