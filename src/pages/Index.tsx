import { useState } from 'react';
import Icon from '@/components/ui/icon';
import { Button } from '@/components/ui/button';
import { toast } from '@/hooks/use-toast';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

const GENERATE_URL = 'https://functions.poehali.dev/ac2d299a-3ec2-4e40-86a9-758864f85230';

const HERO_IMG =
  'https://cdn.poehali.dev/projects/691722e8-7b77-423b-9fd2-f67bc3d3851d/files/a02861e5-cc7a-4cf5-9b0a-0b21a83dbc6a.jpg';

const NAV = [
  { label: 'Главная', href: '#hero' },
  { label: 'Конструктор', href: '#constructor' },
  { label: 'Шаблоны', href: '#templates' },
  { label: 'Мои проекты', href: '#projects' },
  { label: 'Документация', href: '#docs' },
  { label: 'Контакты', href: '#contacts' },
];

const FEATURES = [
  {
    icon: 'Sparkles',
    title: 'Генерация дизайна',
    text: 'Опишите идею словами — ИИ соберёт макет, подберёт цвета, шрифты и расставит блоки.',
  },
  {
    icon: 'PenLine',
    title: 'Контент за секунды',
    text: 'Тексты, заголовки и изображения создаются автоматически под вашу тематику.',
  },
  {
    icon: 'Wand2',
    title: 'Умный конструктор',
    text: 'Перетаскивайте блоки, а ИИ подсказывает улучшения прямо в процессе редактирования.',
  },
  {
    icon: 'Rocket',
    title: 'Мгновенная публикация',
    text: 'Один клик — и сайт в сети с SSL, своим доменом и оптимизацией под поиск.',
  },
];

const TEMPLATES = [
  { name: 'Лендинг стартапа', tag: 'Бизнес', gradient: 'from-violet-500 to-fuchsia-500', prompt: 'Современный лендинг для технологического стартапа' },
  { name: 'Портфолио', tag: 'Креатив', gradient: 'from-cyan-400 to-blue-500', prompt: 'Минималистичное портфолио дизайнера с проектами' },
  { name: 'Интернет-магазин', tag: 'E-commerce', gradient: 'from-pink-500 to-rose-500', prompt: 'Интернет-магазин модной одежды с каталогом' },
  { name: 'Блог', tag: 'Медиа', gradient: 'from-amber-400 to-orange-500', prompt: 'Личный блог о путешествиях и фотографии' },
  { name: 'SaaS-платформа', tag: 'Tech', gradient: 'from-emerald-400 to-teal-500', prompt: 'Сайт SaaS-сервиса для управления задачами' },
  { name: 'Событие', tag: 'Афиша', gradient: 'from-indigo-500 to-purple-500', prompt: 'Промо-сайт музыкального фестиваля' },
];

const STEPS = [
  { n: '01', title: 'Опишите идею', text: 'Расскажите, какой сайт нужен — простыми словами.' },
  { n: '02', title: 'ИИ создаёт', text: 'Генерируем дизайн, структуру и контент за минуту.' },
  { n: '03', title: 'Публикуйте', text: 'Редактируйте и запускайте в один клик.' },
];

interface SiteSection {
  heading: string;
  text: string;
}
interface GeneratedSite {
  title: string;
  tagline: string;
  sections: SiteSection[];
  cta: string;
  colors?: { primary: string; accent: string };
}

const Index = () => {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<GeneratedSite | null>(null);
  const [open, setOpen] = useState(false);

  const scrollTo = (href: string) => {
    document.querySelector(href)?.scrollIntoView({ behavior: 'smooth' });
  };

  const generate = async (text: string) => {
    const value = text.trim();
    if (!value) {
      toast({ title: 'Опишите свой сайт', description: 'Введите, что хотите создать.' });
      return;
    }
    setLoading(true);
    setResult(null);
    setOpen(true);
    try {
      const res = await fetch(GENERATE_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: value }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Ошибка генерации');
      setResult(data.site);
    } catch (e) {
      setOpen(false);
      toast({
        title: 'Не удалось сгенерировать',
        description: e instanceof Error ? e.message : 'Попробуйте ещё раз.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground overflow-x-hidden">
      {/* NAV */}
      <header className="fixed top-0 inset-x-0 z-50">
        <div className="container flex items-center justify-between h-20">
          <button onClick={() => scrollTo('#hero')} className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary to-secondary glow flex items-center justify-center">
              <Icon name="Atom" className="text-white" size={20} />
            </div>
            <span className="font-display font-extrabold text-xl tracking-tight">
              Nebula<span className="text-gradient">AI</span>
            </span>
          </button>
          <nav className="hidden lg:flex items-center gap-8">
            {NAV.map((item) => (
              <button
                key={item.label}
                onClick={() => scrollTo(item.href)}
                className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                {item.label}
              </button>
            ))}
          </nav>
          <div className="flex items-center gap-3">
            <button
              onClick={() => scrollTo('#profile')}
              className="hidden sm:flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <Icon name="User" size={18} />
              Профиль
            </button>
            <Button
              onClick={() => scrollTo('#constructor')}
              className="rounded-full bg-gradient-to-r from-primary to-accent hover:opacity-90 font-semibold text-white"
            >
              Начать бесплатно
            </Button>
          </div>
        </div>
      </header>

      {/* HERO + CONSTRUCTOR */}
      <section id="hero" className="relative pt-40 pb-28">
        <div id="constructor" className="absolute -top-20" />
        <div className="absolute inset-0 grid-bg pointer-events-none" />
        <div className="absolute inset-0 aurora pointer-events-none" />
        <img
          src={HERO_IMG}
          alt=""
          className="absolute -right-20 top-24 w-[480px] max-w-[60vw] opacity-80 animate-float rounded-full pointer-events-none select-none"
        />
        <div className="container relative">
          <div className="max-w-3xl animate-fade-in">
            <div className="inline-flex items-center gap-2 glass rounded-full px-4 py-1.5 mb-7 text-sm">
              <span className="w-2 h-2 rounded-full bg-secondary animate-pulse-glow" />
              Новое поколение веб-разработки
            </div>
            <h1 className="font-display font-black text-5xl md:text-7xl leading-[1.05] tracking-tight">
              Сайт мечты <br />
              <span className="text-gradient">по одному описанию</span>
            </h1>
            <p className="mt-6 text-lg text-muted-foreground max-w-xl">
              Опишите, что хотите — искусственный интеллект сгенерирует дизайн,
              тексты и структуру за минуту. Без кода и дизайнеров.
            </p>

            {/* PROMPT BOX */}
            <div className="mt-10 glass rounded-2xl p-3 flex flex-col sm:flex-row gap-3 max-w-2xl">
              <div className="flex items-center gap-3 flex-1 px-3">
                <Icon name="Sparkles" className="text-primary shrink-0" size={22} />
                <input
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && generate(prompt)}
                  placeholder="Создай лендинг для кофейни в стиле минимализм..."
                  className="bg-transparent outline-none w-full py-3 placeholder:text-muted-foreground"
                />
              </div>
              <Button
                onClick={() => generate(prompt)}
                disabled={loading}
                className="rounded-xl h-12 px-7 bg-gradient-to-r from-primary to-accent hover:opacity-90 font-semibold text-white"
              >
                {loading ? (
                  <Icon name="Loader2" size={18} className="mr-2 animate-spin" />
                ) : (
                  <Icon name="Wand2" size={18} className="mr-2" />
                )}
                {loading ? 'Создаю...' : 'Создать'}
              </Button>
            </div>
            <div className="mt-5 flex flex-wrap gap-3 text-sm text-muted-foreground">
              <span>Популярное:</span>
              {['Портфолио фотографа', 'Магазин одежды', 'Сайт-визитка'].map((t) => (
                <button
                  key={t}
                  onClick={() => { setPrompt(t); generate(t); }}
                  className="hover:text-foreground transition-colors underline-offset-4 hover:underline"
                >
                  {t}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section className="container py-24">
        <div className="max-w-2xl mb-14">
          <p className="text-secondary font-semibold mb-3">Возможности ИИ</p>
          <h2 className="font-display font-extrabold text-4xl md:text-5xl tracking-tight">
            Всё, чтобы запустить сайт <span className="text-gradient">без усилий</span>
          </h2>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {FEATURES.map((f, i) => (
            <div
              key={f.title}
              style={{ animationDelay: `${i * 80}ms` }}
              className="glass rounded-2xl p-6 hover-scale animate-fade-in"
            >
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary/30 to-accent/30 flex items-center justify-center mb-5">
                <Icon name={f.icon} className="text-primary" size={24} />
              </div>
              <h3 className="font-display font-bold text-lg mb-2">{f.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">{f.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section id="docs" className="container py-12">
        <div className="grid md:grid-cols-3 gap-5">
          {STEPS.map((s) => (
            <div key={s.n} className="relative glass rounded-2xl p-8 overflow-hidden">
              <span className="font-display font-black text-7xl text-gradient opacity-30 absolute -top-2 right-4">
                {s.n}
              </span>
              <h3 className="font-display font-bold text-xl mb-2 relative">{s.title}</h3>
              <p className="text-muted-foreground relative">{s.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* TEMPLATES */}
      <section id="templates" className="container py-24">
        <div className="flex flex-wrap items-end justify-between gap-4 mb-12">
          <div>
            <p className="text-secondary font-semibold mb-3">Шаблоны</p>
            <h2 className="font-display font-extrabold text-4xl md:text-5xl tracking-tight">
              Стартуйте с готового
            </h2>
          </div>
          <Button
            onClick={() => scrollTo('#constructor')}
            variant="outline"
            className="rounded-full border-border hover:bg-muted"
          >
            Все шаблоны
            <Icon name="ArrowRight" size={18} className="ml-2" />
          </Button>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {TEMPLATES.map((t, i) => (
            <button
              key={t.name}
              onClick={() => generate(t.prompt)}
              style={{ animationDelay: `${i * 60}ms` }}
              className="group relative rounded-2xl overflow-hidden border border-border hover-scale animate-fade-in cursor-pointer text-left"
            >
              <div className={`h-44 bg-gradient-to-br ${t.gradient} relative`}>
                <div className="absolute inset-0 grid-bg opacity-40" />
                <Icon
                  name="LayoutTemplate"
                  className="absolute bottom-4 right-4 text-white/70"
                  size={32}
                />
              </div>
              <div className="p-5 bg-card flex items-center justify-between">
                <div>
                  <span className="text-xs text-muted-foreground">{t.tag}</span>
                  <h3 className="font-display font-bold text-lg">{t.name}</h3>
                </div>
                <div className="w-9 h-9 rounded-full bg-muted flex items-center justify-center group-hover:bg-primary transition-colors">
                  <Icon name="ArrowUpRight" size={18} />
                </div>
              </div>
            </button>
          ))}
        </div>
      </section>

      {/* PROJECTS / PROFILE */}
      <section id="projects" className="container py-20">
        <div id="profile" className="absolute -mt-24" />
        <div className="glass rounded-3xl p-10 md:p-14 text-center">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/30 to-accent/30 flex items-center justify-center mx-auto mb-6">
            <Icon name="FolderOpen" className="text-primary" size={30} />
          </div>
          <h2 className="font-display font-extrabold text-3xl md:text-4xl tracking-tight mb-3">
            Здесь появятся ваши проекты
          </h2>
          <p className="text-muted-foreground max-w-md mx-auto">
            Создайте первый сайт через конструктор — он автоматически сохранится в этом разделе.
          </p>
          <Button
            onClick={() => scrollTo('#constructor')}
            className="mt-7 rounded-full bg-gradient-to-r from-primary to-accent hover:opacity-90 font-semibold text-white"
          >
            <Icon name="Plus" size={18} className="mr-2" />
            Создать проект
          </Button>
        </div>
      </section>

      {/* CTA / CONTACTS */}
      <section id="contacts" className="container py-16">
        <div className="relative glass rounded-3xl p-12 md:p-16 text-center overflow-hidden">
          <div className="absolute inset-0 aurora opacity-70" />
          <div className="relative">
            <h2 className="font-display font-black text-4xl md:text-6xl tracking-tight">
              Готовы создать <span className="text-gradient">свой сайт?</span>
            </h2>
            <p className="mt-5 text-muted-foreground max-w-xl mx-auto text-lg">
              Присоединяйтесь к тысячам, кто запустил проект без единой строчки кода.
            </p>
            <Button
              onClick={() => scrollTo('#constructor')}
              className="mt-8 rounded-full h-14 px-10 text-base bg-gradient-to-r from-primary to-accent hover:opacity-90 font-semibold text-white glow"
            >
              Запустить конструктор
              <Icon name="Rocket" size={20} className="ml-2" />
            </Button>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-border mt-12">
        <div className="container py-12 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
              <Icon name="Atom" className="text-white" size={18} />
            </div>
            <span className="font-display font-extrabold">
              Nebula<span className="text-gradient">AI</span>
            </span>
          </div>
          <p className="text-sm text-muted-foreground">
            © 2026 NebulaAI. Создано с помощью искусственного интеллекта.
          </p>
          <div className="flex gap-4">
            {['Send', 'Github', 'Twitter'].map((s) => (
              <button
                key={s}
                className="w-9 h-9 rounded-full glass flex items-center justify-center hover:text-primary transition-colors"
              >
                <Icon name={s} size={18} />
              </button>
            ))}
          </div>
        </div>
      </footer>

      {/* RESULT DIALOG */}
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="glass border-border max-w-2xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-display text-2xl flex items-center gap-2">
              <Icon name="Sparkles" className="text-primary" size={22} />
              {loading ? 'ИИ создаёт ваш сайт...' : 'Ваш сайт готов'}
            </DialogTitle>
          </DialogHeader>

          {loading && (
            <div className="py-16 flex flex-col items-center gap-4 text-muted-foreground">
              <Icon name="Loader2" size={40} className="animate-spin text-primary" />
              <p>Генерируем структуру и контент...</p>
            </div>
          )}

          {!loading && result && (
            <div className="space-y-5 animate-fade-in">
              <div
                className="rounded-2xl p-7 text-center"
                style={{
                  background: `linear-gradient(135deg, ${result.colors?.primary || '#8b5cf6'}, ${result.colors?.accent || '#ec4899'})`,
                }}
              >
                <h3 className="font-display font-black text-3xl text-white">{result.title}</h3>
                <p className="text-white/90 mt-2">{result.tagline}</p>
              </div>
              {result.sections?.map((s, i) => (
                <div key={i} className="glass rounded-xl p-5">
                  <h4 className="font-display font-bold text-lg mb-1">{s.heading}</h4>
                  <p className="text-muted-foreground text-sm leading-relaxed">{s.text}</p>
                </div>
              ))}
              <Button className="w-full rounded-xl h-12 bg-gradient-to-r from-primary to-accent hover:opacity-90 font-semibold text-white">
                {result.cta || 'Опубликовать сайт'}
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Index;
