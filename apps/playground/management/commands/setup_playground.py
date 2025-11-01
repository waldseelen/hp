from django.core.management.base import BaseCommand

from apps.playground.models import CodeTemplate, ProgrammingLanguage


class Command(BaseCommand):
    help = "Setup initial playground data with languages and templates"

    def handle(self, *args, **options):
        self.stdout.write("Setting up CodePlay playground...")

        # Create programming languages
        languages_data = [
            {
                "name": "Python",
                "icon": "PY",
                "tagline": "AI'nin dili",
                "extension": "py",
                "order": 1,
            },
            {
                "name": "JavaScript",
                "icon": "JS",
                "tagline": "Web'in krali",
                "extension": "js",
                "order": 2,
            },
            {
                "name": "C",
                "icon": "C",
                "tagline": "Hizli ve guclu",
                "extension": "c",
                "order": 3,
            },
            {
                "name": "C++",
                "icon": "C++",
                "tagline": "Oyunlar ve AI icin",
                "extension": "cpp",
                "order": 4,
            },
            {
                "name": "C#",
                "icon": "C#",
                "tagline": "Microsoft'un gucu",
                "extension": "cs",
                "order": 5,
            },
        ]

        for lang_data in languages_data:
            language, created = ProgrammingLanguage.objects.get_or_create(
                name=lang_data["name"], defaults=lang_data
            )
            if created:
                self.stdout.write(f"[+] Created language: {language}")
            else:
                self.stdout.write(f"[!] Language already exists: {language}")

        # Create code templates
        python_lang = ProgrammingLanguage.objects.get(name="Python")
        javascript_lang = ProgrammingLanguage.objects.get(name="JavaScript")
        cpp_lang = ProgrammingLanguage.objects.get(name="C++")
        c_lang = ProgrammingLanguage.objects.get(name="C")
        csharp_lang = ProgrammingLanguage.objects.get(name="C#")

        templates_data = [
            {
                "name": "Hello World",
                "description": "Python ile ilk program",
                "language": python_lang,
                "emoji": "[Hello]",
                "is_featured": True,
                "code": """print("Hello, World!")
print("CodePlay'e hoş geldin!")

# Bu basit program ile başlayalım
name = input("Adın nedir? ")
print(f"Merhaba {name}! Hoş geldin CodePlay'e!")""",
            },
            {
                "name": "Basit Hesap Makinesi",
                "description": "Python hesap makinesi",
                "language": python_lang,
                "emoji": "[CALC]",
                "is_featured": True,
                "code": """# Basit Hesap Makinesi
def hesapla(a, b, islem):
    if islem == '+':
        return a + b
    elif islem == '-':
        return a - b
    elif islem == '*':
        return a * b
    elif islem == '/':
        return a / b if b != 0 else "Sıfıra bölme hatası!"
    else:
        return "Geçersiz işlem"

# Test edelim
print("=== CodePlay Hesap Makinesi ===")
print("5 + 3 =", hesapla(5, 3, '+'))
print("10 - 4 =", hesapla(10, 4, '-'))
print("6 * 7 =", hesapla(6, 7, '*'))
print("15 / 3 =", hesapla(15, 3, '/'))""",
            },
            {
                "name": "AI Chatbot",
                "description": "Basit AI chatbot yapısı",
                "language": python_lang,
                "emoji": "[BOT]",
                "is_featured": True,
                "code": """import random

class BasitChatbot:
    def __init__(self):
        self.cevaplar = {
            'merhaba': ['Merhaba!', 'Selam!', 'Hey!'],
            'nasılsın': ['İyiyim, teşekkürler!', 'Harika!', 'Çok iyi!'],
            'ne yapıyorsun': ['Kod yazıyorum', 'Öğreniyorum', 'Düşünüyorum'],
            'görüşürüz': ['Hoşçakal!', 'Görüşürüz!', 'Bay bay!']
        }

    def cevap_ver(self, mesaj):
        mesaj = mesaj.lower()
        for anahtar in self.cevaplar:
            if anahtar in mesaj:
                return random.choice(self.cevaplar[anahtar])
        return "Anlamadım, başka şey söyleyebilir misin?"

# Chatbot'u test edelim
bot = BasitChatbot()
print("🤖 CodePlay Bot: Merhaba! Benimle konuşabilirsin.")
print("Bot:", bot.cevap_ver("merhaba"))
print("Bot:", bot.cevap_ver("nasılsın"))
print("Bot:", bot.cevap_ver("ne yapıyorsun"))""",
            },
            {
                "name": "Web Sitesi Temeli",
                "description": "HTML/CSS/JS ile basit site",
                "language": javascript_lang,
                "emoji": "[WEB]",
                "is_featured": True,
                "code": """// Web sitesi için JavaScript
document.addEventListener('DOMContentLoaded', function() {
    console.log('🌟 CodePlay Web Sitesi Yüklendi!');

    // Dinamik içerik oluştur
    const container = document.body;

    // Başlık ekle
    const title = document.createElement('h1');
    title.textContent = '🌟 CodePlay Web Sitesi';
    title.style.color = '#FFD700';
    title.style.textAlign = 'center';
    container.appendChild(title);

    // Buton ekle
    const button = document.createElement('button');
    button.textContent = 'Tıkla Beni!';
    button.style.padding = '10px 20px';
    button.style.fontSize = '16px';
    button.style.backgroundColor = '#4CAF50';
    button.style.color = 'white';
    button.style.border = 'none';
    button.style.borderRadius = '5px';
    button.style.cursor = 'pointer';

    // Butona tıklama eventi
    let count = 0;
    button.addEventListener('click', function() {
        count++;
        alert(`🎉 Butona ${count} kez tıkladın!`);
    });

    container.appendChild(button);
});""",
            },
            {
                "name": "Sayı Tahmin Oyunu",
                "description": "C++ ile basit oyun",
                "language": cpp_lang,
                "emoji": "[GAME]",
                "is_featured": True,
                "code": """#include <iostream>
#include <random>
#include <string>

using namespace std;

int main() {
    cout << "🎮 CodePlay Sayı Tahmin Oyunu!" << endl;
    cout << "1-100 arası bir sayı tuttum, tahmin et!" << endl;

    // Random sayı üret
    random_device rd;
    mt19937 gen(rd());
    uniform_int_distribution<> dis(1, 100);
    int gizliSayi = dis(gen);

    int tahmin;
    int deneme = 0;

    do {
        cout << "Tahminin: ";
        cin >> tahmin;
        deneme++;

        if (tahmin < gizliSayi) {
            cout << "⬆️ Daha büyük bir sayı söyle!" << endl;
        } else if (tahmin > gizliSayi) {
            cout << "⬇️ Daha küçük bir sayı söyle!" << endl;
        } else {
            cout << "🎉 Tebrikler! " << deneme << " denemede bildin!" << endl;
            cout << "Sayı: " << gizliSayi << endl;
        }
    } while (tahmin != gizliSayi);

    return 0;
}""",
            },
            {
                "name": "Hello World C",
                "description": "C ile ilk program",
                "language": c_lang,
                "emoji": "[FAST]",
                "is_featured": False,
                "code": """#include <stdio.h>

int main() {
    printf("⚡ CodePlay ile C Programlama!\\n");
    printf("Hızlı ve güçlü C diline hoş geldin!\\n");

    // Basit hesaplama
    int a = 10, b = 20;
    int toplam = a + b;

    printf("%d + %d = %d\\n", a, b, toplam);

    return 0;
}""",
            },
            {
                "name": "C# Console App",
                "description": "C# konsol uygulaması",
                "language": csharp_lang,
                "emoji": "[WORK]",
                "is_featured": False,
                "code": """using System;

namespace CodePlayApp
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("💼 CodePlay C# Uygulaması!");
            Console.WriteLine("Microsoft'un gücü ile programlama");

            // Kullanıcıdan isim al
            Console.Write("Adınız: ");
            string name = Console.ReadLine();

            Console.WriteLine($"Merhaba {name}!");
            Console.WriteLine("C# ile neler yapabilirsin:");
            Console.WriteLine("• Web uygulamaları (ASP.NET)");
            Console.WriteLine("• Mobil uygulamalar (Xamarin)");
            Console.WriteLine("• Oyunlar (Unity)");
            Console.WriteLine("• Desktop uygulamalar (WPF)");

            Console.WriteLine("\\nDevam etmek için bir tuşa basın...");
            Console.ReadKey();
        }
    }
}""",
            },
        ]

        for template_data in templates_data:
            template, created = CodeTemplate.objects.get_or_create(
                name=template_data["name"],
                language=template_data["language"],
                defaults=template_data,
            )
            if created:
                self.stdout.write(f"[+] Created template: {template}")
            else:
                self.stdout.write(f"[!] Template already exists: {template}")

        self.stdout.write(self.style.SUCCESS("CodePlay playground setup completed!"))
        self.stdout.write("You can now visit /playground/ to start coding!")
