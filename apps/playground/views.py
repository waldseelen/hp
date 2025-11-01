import json
import os
import subprocess
import tempfile
import time

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt

from .models import CodeSnippet, CodeTemplate, ProgrammingLanguage


def index(request):
    """Main playground page"""
    languages = ProgrammingLanguage.objects.filter(is_active=True)
    templates = CodeTemplate.objects.filter(is_featured=True)[:6]
    recent_snippets = CodeSnippet.objects.filter(is_public=True)[:10]

    context = {
        "languages": languages,
        "templates": templates,
        "recent_snippets": recent_snippets,
    }
    return render(request, "playground/index.html", context)


def editor(request, language_id=None):
    """Code editor page"""
    languages = ProgrammingLanguage.objects.filter(is_active=True)
    selected_language = None

    if language_id:
        selected_language = get_object_or_404(ProgrammingLanguage, id=language_id)
    else:
        selected_language = languages.first()

    templates = CodeTemplate.objects.filter(language=selected_language)

    context = {
        "languages": languages,
        "selected_language": selected_language,
        "templates": templates,
    }
    return render(request, "playground/editor.html", context)


@csrf_exempt
def execute_code(request):
    """Execute code and return results"""
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)

    try:
        data = json.loads(request.body)
        code = data.get("code", "").strip()
        language_id = data.get("language_id")

        if not code or not language_id:
            return JsonResponse({"error": "Code and language required"}, status=400)

        language = get_object_or_404(ProgrammingLanguage, id=language_id)

        # Execute code based on language
        result = _execute_code_safely(code, language)

        return JsonResponse(result)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def _execute_code_safely(code, language):  # noqa: C901
    """Safely execute code in a sandbox"""
    start_time = time.time()

    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=f".{language.extension}", delete=False
        ) as f:
            f.write(code)
            temp_file = f.name

        # Simple execution based on language
        if language.name.lower() == "python":
            result = subprocess.run(
                ["python", temp_file],
                capture_output=True,
                text=True,
                timeout=10,  # 10 second timeout
            )
        elif language.name.lower() == "javascript":
            result = subprocess.run(
                ["node", temp_file], capture_output=True, text=True, timeout=10
            )
        elif language.name.lower() in ["c", "c++"]:
            # Compile first
            exe_file = temp_file.replace(f".{language.extension}", ".exe")
            compiler = "gcc" if language.name.lower() == "c" else "g++"

            compile_result = subprocess.run(
                [compiler, temp_file, "-o", exe_file],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if compile_result.returncode != 0:
                return {
                    "success": False,
                    "output": "",
                    "error": f"Compilation error:\n{compile_result.stderr}",
                    "execution_time": (time.time() - start_time) * 1000,
                }

            # Run executable
            result = subprocess.run(
                [exe_file], capture_output=True, text=True, timeout=10
            )

            # Clean up exe file
            try:
                os.unlink(exe_file)
            except OSError:
                # File may already be deleted
                pass

        elif language.name.lower() == "c#":
            # Basic C# execution (requires mono or dotnet)
            result = subprocess.run(
                ["dotnet", "run", "--project", temp_file],
                capture_output=True,
                text=True,
                timeout=15,
            )
        else:
            return {
                "success": False,
                "output": "",
                "error": f"Language {language.name} not yet supported for execution",
                "execution_time": 0,
            }

        execution_time = (time.time() - start_time) * 1000

        # Clean up temp file
        try:
            os.unlink(temp_file)
        except OSError:
            # File may already be deleted
            pass

        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else "",
            "execution_time": execution_time,
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": "Code execution timed out (10 seconds limit)",
            "execution_time": 10000,
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": f"Execution error: {str(e)}",
            "execution_time": (time.time() - start_time) * 1000,
        }


@csrf_exempt
def save_snippet(request):
    """Save code snippet"""
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)

    try:
        data = json.loads(request.body)

        snippet = CodeSnippet.objects.create(
            title=data.get("title", ""),
            language_id=data.get("language_id"),
            code=data.get("code", ""),
            output=data.get("output", ""),
            user=request.user if request.user.is_authenticated else None,
            is_public=data.get("is_public", False),
        )

        return JsonResponse(
            {
                "success": True,
                "snippet_id": str(snippet.id),
                "share_url": snippet.share_url,
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def snippet_detail(request, pk):
    """View a specific code snippet"""
    snippet = get_object_or_404(CodeSnippet, id=pk)

    # Increment view count
    snippet.views += 1
    snippet.save(update_fields=["views"])

    context = {
        "snippet": snippet,
    }
    return render(request, "playground/snippet_detail.html", context)


def gallery(request):
    """Public code gallery"""
    snippets = CodeSnippet.objects.filter(is_public=True).select_related(
        "language", "user"
    )
    languages = ProgrammingLanguage.objects.filter(is_active=True)

    # Filter by language
    language_filter = request.GET.get("language")
    if language_filter:
        snippets = snippets.filter(language__name=language_filter)

    # Search
    search = request.GET.get("search")
    if search:
        snippets = snippets.filter(title__icontains=search)

    context = {
        "snippets": snippets,
        "languages": languages,
        "current_language": language_filter,
        "search_query": search,
    }
    return render(request, "playground/gallery.html", context)


def get_template(request, template_id):
    """Get code template"""
    template = get_object_or_404(CodeTemplate, id=template_id)

    return JsonResponse(
        {
            "name": template.name,
            "description": template.description,
            "code": template.code,
            "language_id": template.language.id,
        }
    )
