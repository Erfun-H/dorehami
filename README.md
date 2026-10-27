# دورهمی (Dorehami)

وب‌اپلیکیشنی برای هماهنگی قرارهای جمعی: میزبان یک دورهمی می‌سازد، لینک دعوت را با دوستانش به اشتراک می‌گذارد، همه تاریخ و ساعت پیشنهاد می‌دهند، روی پیشنهادها توافق می‌کنند و در نهایت میزبان زمان نهایی را قطعی می‌کند.

## امکانات

- **حساب کاربری** — ثبت‌نام و login با ایمیل و رمز عبور.
- **ساخت دورهمی** — عنوان و توضیحات دلخواه؛ هر دورهمی یک لینک دعوت با توکن تصادفی می‌گیرد.
- **عضویت با لینک دعوت** — کاربر واردشده که لینک معتبر یک دورهمی فعال را باز کند، به‌عنوان شرکت‌کننده اضافه می‌شود.
- **پیشنهاد تاریخ** — شرکت‌کننده‌ها با datepicker جلالی پیشنهاد تاریخ/ساعت ثبت می‌کنند؛ هر پیشنهاد فقط توسط سازنده‌اش قابل ویرایش است.
- **توافق (Agreement)** — هر شرکت‌کننده روی هر پیشنهاد می‌تواند موافق باشد یا موافقتش را پس بگیرد.
- **قطعی کردن (Finalize)** — فقط میزبان می‌تواند دورهمی را نهایی کند، و فقط وقتی حداقل یک توافق از سوی کسی غیر از خودش ثبت شده باشد. بعد از finalize همه پیشنهادها و توافق‌ها قفل می‌شوند و لینک دعوت دیگر عضو جدید نمی‌پذیرد.

## تکنولوژی‌ها

- Python 3.12 و Django 6
- PostgreSQL با psycopg 3
- django-jalali برای ذخیره و نمایش تاریخ شمسی (`jDateField` و فیلتر قالب `jformat`) + ویجت `jalali-datepicker`
- Tailwind CSS 4 — سورس در `src/theme/`، خروجی build شده در `src/static/css/app.css`
- Ruff برای lint و format، pytest و pytest-django برای تست

## راه‌اندازی

پیش‌نیازها: Python 3.12 و PostgreSQL در حال اجرا.

```bash
# virtualenv و نصب وابستگی‌ها
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

# ساخت دیتابیس
createdb dorehami

# environment variables
cp .env.example .env.dev   # مقادیر را مطابق سیستم خودتان تنظیم کنید
set -a; source .env.dev; set +a

# اعمال مایگریشن‌ها و اجرای سرور
python src/manage.py migrate
python src/manage.py runserver
```

اپلیکیشن روی `http://127.0.0.1:8000/` بالا می‌آید.

اگر خواستید CSS را دوباره build کنید (تغییر در `src/theme/input.css`):

```bash
cd src/theme && npm install && npm run build:css
```

### Environment variables

| متغیر | توضیح |
|---|---|
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | مشخصات اتصال به PostgreSQL |
| `POSTGRES_HOST` / `POSTGRES_PORT` | آدرس و پورت دیتابیس |
| `DJANGO_SECRET_KEY` | secret key جنگو (پیش‌فرض dev فقط برای توسعه است) |
| `DJANGO_DEBUG` | `true` فقط برای توسعه؛ پیش‌فرض `False` |
| `DJANGO_ALLOWED_HOSTS` | لیست hostهای مجاز با کاما (مبنای `CSRF_TRUSTED_ORIGINS` هم هست) |
| `DJANGO_ADMIN_PATH` | مسیر پنل ادمین، پیش‌فرض `admin/` |

## تست و lint

```bash
ruff check src
ruff format --check src
PYTHONPATH=src pytest
```

تست‌ها سناریوهای کلیدی را پوشش می‌دهند: ساخت حساب، محافظت لینک دعوت، عضویت، دسترسی‌های پیشنهاد، جایگزینی توافق، تساوی پیشنهادها و محدودیت‌های event نهایی‌شده.

## ساختار پروژه

```
src/
├── config/        # تنظیمات و URLهای اصلی جنگو
├── accounts/      # User سفارشی، signup / login / logout
├── events/        # مدل‌های Event، Participation، Suggestion، Agreement
│                  #   + سرویس‌های هماهنگی و templatetagهای تاریخ جلالی
├── templates/     # قالب‌های فارسی/RTL
├── static/        # CSS، JS، فونت‌ها و کتابخانه‌های vendor
└── manage.py
specs/             # مشخصات و طرح featureها (spec-driven)
```

## گردش کار

1. میزبان ثبت‌نام می‌کند و event می‌سازد.
2. لینک دعوت را برای مهمان‌ها می‌فرستد.
3. مهمان‌ها با login و بازکردن لینک، عضو event می‌شوند.
4. هر کس تاریخ‌های پیشنهادی خودش را ثبت می‌کند و روی پیشنهادهای دیگران توافق می‌کند.
5. وقتی حداقل یک توافقِ غیرمیزبان ثبت شده باشد، میزبان event را finalize می‌کند و پیشنهاد منتخب به‌عنوان پیشنهاد نهایی ثبت می‌شود.
