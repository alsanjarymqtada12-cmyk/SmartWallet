import flet as ft
import requests
from datetime import datetime

# رابط قاعدة بياناتك السحابية جاهز (بين علامتي تنصيص)
FIREBASE_URL = "https://smart-wallet-14aaa-default-rtdb.firebaseio.com/data.json"
APP_VERSION = "2.0.0 (Cloud Edition)"

DEFAULT_DATA = {
    "settings": {
        "app_title": "نظام الإدارة المالية",
        "mode": "group",
        "category_type": "dorm",
        "categories": ["عام"],
        "allocations": {},
        "is_setup_done": False
    },
    "budget": {
        "current_balance": 0,
        "total_collected": 0,
        "category_balances": {}
    },
    "expenses_history": []
}


# ==========================================
# محرك الخزن السحابي (Cloud Storage Engine)
# ==========================================
def load_data():
    try:
        response = requests.get(FIREBASE_URL)
        if response.status_code == 200 and response.json() is not None:
            data = response.json()
            if "settings" not in data: data["settings"] = DEFAULT_DATA["settings"]
            if "budget" in data and "category_balances" not in data["budget"]:
                data["budget"]["category_balances"] = {c: 0 for c in data["settings"].get("categories", [])}
            if "expenses_history" not in data: data["expenses_history"] = []
            return data
    except Exception as e:
        print("خطأ في الاتصال بالسحابة:", e)
    return DEFAULT_DATA


def save_data(data):
    try:
        requests.put(FIREBASE_URL, json=data)
    except Exception as e:
        print("خطأ في رفع البيانات للسحابة:", e)


# ==========================================
# الواجهة الرئيسية للتطبيق
# ==========================================
def main(page: ft.Page):
    page.title = "النظام المالي الذكي (السحابي)"
    page.theme_mode = ft.ThemeMode.DARK
    page.rtl = True
    page.window_width = 480
    page.window_height = 850
    page.padding = 20
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO

    data = load_data()

    def show_about_dialog(e):
        dlg = ft.AlertDialog(
            title=ft.Text("عن التطبيق", weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_300),
            content=ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.CLOUD_DONE, size=50, color=ft.colors.BLUE_400),
                    ft.Text("المحفظة الذكية السحابية", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(f"الإصدار: {APP_VERSION}", size=12, color=ft.colors.GREY_400),
                    ft.Divider(),
                    ft.Text("نظام مركزي متصل بقاعدة بيانات سحابية لحظية لمزامنة المصاريف بين جميع أفراد الشقة.",
                            text_align=ft.TextAlign.CENTER, size=14),
                    ft.Container(height=10),
                    ft.Text("تطوير: المهندس مقتدى ابن المهندس مثنى", weight=ft.FontWeight.BOLD,
                            color=ft.colors.GREEN_400),
                    ft.Text("جامعة سومر - هندسة الاتصالات", size=12, color=ft.colors.GREY_400),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                width=320, height=250
            ),
            actions=[ft.TextButton("إغلاق", on_click=lambda e: setattr(page.dialog, 'open', False) or page.update())]
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    page.appbar = ft.AppBar(
        leading=ft.Icon(ft.icons.CLOUD_SYNC, color=ft.colors.BLUE_200),
        leading_width=40,
        title=ft.Text("المحفظة السحابية", size=20, weight=ft.FontWeight.BOLD),
        center_title=False,
        bgcolor=ft.colors.SURFACE_VARIANT,
        actions=[ft.IconButton(ft.icons.INFO_OUTLINE, tooltip="عن المطور", on_click=show_about_dialog)],
    )

    def show_setup_view(e=None):
        page.controls.clear()

        app_title_input = ft.TextField(label="اسم المشروع (مثال: شقة 8)", value=data['settings'].get('app_title', ''),
                                       width=350, border_color=ft.colors.BLUE_400)
        mode_dropdown = ft.Dropdown(
            label="نوع الإدارة", width=350,
            options=[ft.dropdown.Option("group", "مجموعة"), ft.dropdown.Option("personal", "شخصي")],
            value=data['settings'].get('mode', 'group')
        )
        category_type_dropdown = ft.Dropdown(
            label="قالب المصاريف", width=350,
            options=[
                ft.dropdown.Option("dorm", "سكن جامعي (توزيع تلقائي مدروس)"),
                ft.dropdown.Option("custom", "مخصص (توزيع متساوي)")
            ],
            value="dorm"
        )
        custom_categories_input = ft.TextField(label="اكتب الأقسام (افصل بينها بفارزة)", value="طعام, مواصلات, ترفيه",
                                               width=350, visible=False)

        def on_category_type_change(e):
            custom_categories_input.visible = (category_type_dropdown.value == "custom")
            page.update()

        category_type_dropdown.on_change = on_category_type_change

        def save_setup(e):
            data['settings']['app_title'] = app_title_input.value
            data['settings']['mode'] = mode_dropdown.value
            data['settings']['category_type'] = category_type_dropdown.value

            if category_type_dropdown.value == "dorm":
                data['settings']['categories'] = ["مسواك يومي", "مواد أساسية", "منظفات", "طوارئ ولوازم", "أخرى"]
                data['settings']['allocations'] = {"مسواك يومي": 0.50, "مواد أساسية": 0.20, "منظفات": 0.10,
                                                   "طوارئ ولوازم": 0.10, "أخرى": 0.10}
            else:
                cats = [c.strip() for c in custom_categories_input.value.split(",") if c.strip()]
                data['settings']['categories'] = cats if cats else ["عام"]
                fraction = 1.0 / len(data['settings']['categories'])
                data['settings']['allocations'] = {c: fraction for c in data['settings']['categories']}

            data['budget']['category_balances'] = {c: 0 for c in data['settings']['categories']}
            data['settings']['is_setup_done'] = True
            save_data(data)
            show_main_view()

        page.add(
            ft.Container(height=30),
            ft.Icon(ft.icons.CLOUD_UPLOAD, size=60, color=ft.colors.BLUE_400),
            ft.Text("ربط السحابة والإعدادات", size=26, weight=ft.FontWeight.BOLD),
            ft.Text("جاري الاتصال بقاعدة البيانات...", color=ft.colors.GREY_400, size=14),
            ft.Divider(height=30),
            app_title_input,
            mode_dropdown,
            category_type_dropdown,
            custom_categories_input,
            ft.Container(height=20),
            ft.ElevatedButton("حفظ وبدء المزامنة", on_click=save_setup, bgcolor=ft.colors.GREEN_700,
                              color=ft.colors.WHITE, width=350, height=45)
        )
        page.update()

    def show_main_view():
        page.controls.clear()

        nonlocal data
        data = load_data()

        title_text = ft.Text(data['settings']['app_title'], size=26, weight=ft.FontWeight.BOLD,
                             color=ft.colors.BLUE_200)
        balance_text = ft.Text(f"الرصيد الكلي: {int(data['budget']['current_balance'])} دينار", size=24,
                               weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_400)
        status_text = ft.Text("متصل بالسحابة 🟢", size=14, color=ft.colors.GREEN_400, weight=ft.FontWeight.BOLD)

        categories_display = ft.Column(spacing=5, width=350)

        def refresh_categories_display():
            categories_display.controls.clear()
            for cat in data['settings']['categories']:
                bal = data['budget']['category_balances'].get(cat, 0)
                color = ft.colors.GREEN_300 if bal >= 0 else ft.colors.RED_400
                categories_display.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(f"{cat}", width=150, weight=ft.FontWeight.W_500),
                            ft.Text(f"{int(bal)} دينار", color=color, weight=ft.FontWeight.BOLD)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=10, bgcolor=ft.colors.SURFACE_VARIANT, border_radius=8
                    )
                )

        def update_ui(msg=""):
            balance_text.value = f"الرصيد الكلي: {int(data['budget']['current_balance'])} دينار"
            status_text.value = msg
            status_text.color = ft.colors.YELLOW_400
            refresh_categories_display()
            save_data(data)  # رفع التغييرات للسحابة فوراً
            page.update()

        def distribute_funds(amount):
            for cat in data['settings']['categories']:
                pct = data['settings']['allocations'].get(cat, 0)
                data['budget']['category_balances'][cat] = data['budget']['category_balances'].get(cat, 0) + (
                            amount * pct)

        def sync_from_cloud(e):
            nonlocal data
            status_text.value = "جاري المزامنة..."
            status_text.color = ft.colors.GREY_400
            page.update()

            data = load_data()
            update_ui("تمت مزامنة البيانات السحابية 🟢")
            status_text.color = ft.colors.GREEN_400
            page.update()

        def open_manual_deposit(e):
            cat_inputs = []
            for cat in data['settings']['categories']:
                cat_inputs.append(
                    ft.TextField(label=f"مبلغ {cat}", value="0", keyboard_type=ft.KeyboardType.NUMBER, width=250,
                                 text_align=ft.TextAlign.CENTER))

            def save_manual_deposit(e):
                try:
                    total_amount = sum(int(inp.value) if inp.value else 0 for inp in cat_inputs)
                    if total_amount > 0:
                        for i, cat in enumerate(data['settings']['categories']):
                            data['budget']['category_balances'][cat] += int(cat_inputs[i].value)
                        data['budget']['current_balance'] += total_amount
                        data['budget']['total_collected'] += total_amount
                        page.dialog.open = False
                        update_ui(f"✅ تم إيداع وتوزيع {total_amount} دينار يدوياً.")
                except ValueError:
                    pass

            dlg = ft.AlertDialog(
                title=ft.Text("توزيع الأموال يدوياً", size=18, weight=ft.FontWeight.BOLD),
                content=ft.Container(content=ft.Column(cat_inputs, scroll=ft.ScrollMode.AUTO), width=300, height=250),
                actions=[
                    ft.TextButton("إلغاء", on_click=lambda e: setattr(page.dialog, 'open', False) or page.update()),
                    ft.ElevatedButton("إيداع وحفظ", on_click=save_manual_deposit, bgcolor=ft.colors.GREEN_700,
                                      color=ft.colors.WHITE)
                ]
            )
            page.dialog = dlg
            dlg.open = True
            page.update()

        def open_transfer_dialog(e):
            from_cat = ft.Dropdown(label="سحب من قسم",
                                   options=[ft.dropdown.Option(c) for c in data['settings']['categories']], width=140)
            to_cat = ft.Dropdown(label="إضافة إلى قسم",
                                 options=[ft.dropdown.Option(c) for c in data['settings']['categories']], width=140)
            amount_input = ft.TextField(label="المبلغ", keyboard_type=ft.KeyboardType.NUMBER, width=140)

            def execute_transfer(e):
                if not from_cat.value or not to_cat.value or not amount_input.value or from_cat.value == to_cat.value: return
                try:
                    amt = int(amount_input.value)
                    data['budget']['category_balances'][from_cat.value] -= amt
                    data['budget']['category_balances'][to_cat.value] += amt
                    page.dialog.open = False
                    update_ui(f"🔄 تم تحويل {amt} دينار من ({from_cat.value}) إلى ({to_cat.value}).")
                except ValueError:
                    pass

            dlg = ft.AlertDialog(
                title=ft.Text("مناقلة بين الأقسام", size=18, weight=ft.FontWeight.BOLD),
                content=ft.Container(content=ft.Column([
                    ft.Row([from_cat, ft.Icon(ft.icons.ARROW_FORWARD), to_cat], alignment=ft.MainAxisAlignment.CENTER),
                    amount_input
                ], alignment=ft.MainAxisAlignment.CENTER), width=350, height=150),
                actions=[
                    ft.TextButton("إلغاء", on_click=lambda e: setattr(page.dialog, 'open', False) or page.update()),
                    ft.ElevatedButton("تحويل", on_click=execute_transfer, bgcolor=ft.colors.PURPLE_700,
                                      color=ft.colors.WHITE)
                ]
            )
            page.dialog = dlg
            dlg.open = True
            page.update()

        deposit_section = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        buttons_row = ft.Row([
            ft.ElevatedButton("توزيع تلقائي", bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE, expand=True,
                              height=40),
            ft.ElevatedButton("توزيع يدوي", on_click=open_manual_deposit, bgcolor=ft.colors.ORANGE_700,
                              color=ft.colors.WHITE, expand=True, height=40)
        ], width=350)

        if data['settings']['mode'] == "group":
            members_input = ft.TextField(label="عدد الأفراد", value="1", width=120, text_align=ft.TextAlign.CENTER,
                                         keyboard_type=ft.KeyboardType.NUMBER)
            contribution_input = ft.TextField(label="المساهمة", value="10000", width=150,
                                              text_align=ft.TextAlign.CENTER, keyboard_type=ft.KeyboardType.NUMBER)

            def add_group_funds(e):
                try:
                    total = int(members_input.value) * int(contribution_input.value)
                    data['budget']['total_collected'] += total
                    data['budget']['current_balance'] += total
                    distribute_funds(total)
                    update_ui(f"✅ تم جمع {total} دينار وتوزيعها تلقائياً.")
                except:
                    update_ui("❌ تأكد من إدخال الأرقام بشكل صحيح!")

            buttons_row.controls[0].on_click = add_group_funds
            deposit_section.controls.extend(
                [ft.Row([members_input, contribution_input], alignment=ft.MainAxisAlignment.CENTER), buttons_row])
        else:
            personal_amount_input = ft.TextField(label="المبلغ المراد إيداعه", width=350,
                                                 text_align=ft.TextAlign.CENTER, keyboard_type=ft.KeyboardType.NUMBER)

            def add_personal_funds(e):
                try:
                    amount = int(personal_amount_input.value)
                    data['budget']['total_collected'] += amount
                    data['budget']['current_balance'] += amount
                    distribute_funds(amount)
                    personal_amount_input.value = ""
                    update_ui(f"✅ تم إيداع {amount} دينار وتوزيعها تلقائياً.")
                except:
                    update_ui("❌ تأكد من الأرقام!")

            buttons_row.controls[0].on_click = add_personal_funds
            deposit_section.controls.extend([personal_amount_input, buttons_row])

        item_name_input = ft.TextField(label="اسم المصروف", width=150)
        item_price_input = ft.TextField(label="المبلغ", width=100, keyboard_type=ft.KeyboardType.NUMBER)
        item_category_dropdown = ft.Dropdown(label="القسم", width=130,
                                             options=[ft.dropdown.Option(c) for c in data['settings']['categories']],
                                             value=data['settings']['categories'][0])

        def record_expense(e):
            if not item_name_input.value or not item_price_input.value:
                update_ui("⚠️ اكتب اسم المصروف ومبلغه!")
                return
            try:
                price = int(item_price_input.value)
            except:
                update_ui("⚠️ المبلغ يجب أن يكون رقماً!"); return

            if price > data['budget']['current_balance']: update_ui("❌ الرصيد الكلي غير كافي!"); return

            data['budget']['current_balance'] -= price
            cat = item_category_dropdown.value
            data['budget']['category_balances'][cat] -= price

            record = {"item": item_name_input.value, "cost": price, "category": cat,
                      "date": datetime.now().strftime("%Y-%m-%d %H:%M")}
            data['expenses_history'].append(record)

            item_name_input.value = ""
            item_price_input.value = ""
            update_ui(f"🛒 تم صرف {price} على ({record['item']}).")

        def show_history(e):
            def open_edit_dialog(idx, record):
                if page.dialog: page.dialog.open = False
                page.update()

                edit_name = ft.TextField(label="اسم المصروف", value=record['item'], width=280)
                edit_cost = ft.TextField(label="المبلغ", value=str(record['cost']),
                                         keyboard_type=ft.KeyboardType.NUMBER, width=280)
                edit_cat = ft.Dropdown(label="القسم",
                                       options=[ft.dropdown.Option(c) for c in data['settings']['categories']],
                                       value=record.get('category', 'عام'), width=280)

                def save_edit(e):
                    try:
                        new_cost = int(edit_cost.value)
                    except:
                        update_ui("⚠️ المبلغ يجب أن يكون رقماً!"); return

                    old_cost = record['cost']
                    old_cat = record.get('category', 'عام')
                    new_cat = edit_cat.value

                    diff = new_cost - old_cost
                    if diff > data['budget']['current_balance']:
                        update_ui("❌ الرصيد غير كافي لتغطية الزيادة في السعر!")
                        return

                    data['budget']['current_balance'] -= diff
                    if old_cat == new_cat:
                        data['budget']['category_balances'][old_cat] -= diff
                    else:
                        data['budget']['category_balances'][old_cat] += old_cost
                        data['budget']['category_balances'][new_cat] -= new_cost

                    record['item'] = edit_name.value
                    record['cost'] = new_cost
                    record['category'] = new_cat

                    page.dialog.open = False
                    update_ui("✏️ تم تصحيح المصروف بنجاح ومزامنته.")

                def delete_record(e):
                    old_cost = record['cost']
                    old_cat = record.get('category', 'عام')

                    data['budget']['current_balance'] += old_cost
                    data['budget']['category_balances'][old_cat] += old_cost
                    data['expenses_history'].pop(idx)

                    page.dialog.open = False
                    update_ui("🗑️ تم حذف المصروف واسترجاع مبلغه.")

                edit_dlg = ft.AlertDialog(
                    title=ft.Text("تعديل أو حذف المصروف", size=18, weight=ft.FontWeight.BOLD),
                    content=ft.Container(content=ft.Column([edit_name, edit_cost, edit_cat]), width=300, height=220),
                    actions=[
                        ft.TextButton("إلغاء", on_click=lambda e: setattr(page.dialog, 'open', False) or page.update()),
                        ft.IconButton(ft.icons.DELETE_FOREVER, icon_color=ft.colors.RED, tooltip="حذف واسترجاع المبلغ",
                                      on_click=delete_record),
                        ft.ElevatedButton("تحديث السحابة", on_click=save_edit, bgcolor=ft.colors.GREEN_700,
                                          color=ft.colors.WHITE)
                    ]
                )
                page.dialog = edit_dlg
                edit_dlg.open = True
                page.update()

            history_list = ft.ListView(spacing=10, padding=10, height=350)
            if not data['expenses_history']:
                history_list.controls.append(ft.Text("لا توجد مصاريف مسجلة.", color=ft.colors.GREY_400))
            else:
                for idx, rec in reversed(list(enumerate(data['expenses_history']))):
                    cat = rec.get('category', 'عام')
                    row = ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(f"{rec['item']} ({cat})", weight=ft.FontWeight.BOLD),
                                ft.Text(f"{rec['cost']} دينار", color=ft.colors.RED_400, size=13)
                            ], alignment=ft.MainAxisAlignment.START, expand=True),
                            ft.IconButton(ft.icons.EDIT, icon_color=ft.colors.BLUE_400,
                                          on_click=lambda e, i=idx, r=rec: open_edit_dialog(i, r))
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=5, border=ft.border.only(bottom=ft.border.BorderSide(1, ft.colors.GREY_800))
                    )
                    history_list.controls.append(row)

            dlg = ft.AlertDialog(title=ft.Text("سجل المصاريف", weight=ft.FontWeight.BOLD),
                                 content=ft.Container(content=history_list, width=380, height=350))
            page.dialog = dlg
            dlg.open = True
            page.update()

        def confirm_reset(e):
            dlg = ft.AlertDialog(
                title=ft.Text("إعادة ضبط", color=ft.colors.RED),
                content=ft.Text("سيتم مسح كل البيانات من السحابة للبدء من جديد. هل أنت متأكد؟"),
                actions=[
                    ft.TextButton("إلغاء", on_click=lambda e: setattr(page.dialog, 'open', False) or page.update()),
                    ft.TextButton("نعم", on_click=lambda e: [
                        data['budget'].update({'current_balance': 0, 'total_collected': 0, 'category_balances': {}}),
                        data.update({'expenses_history': []}),
                        data['settings'].update({'is_setup_done': False}),
                        save_data(data), setattr(page.dialog, 'open', False), show_setup_view()
                    ], style=ft.ButtonStyle(color=ft.colors.RED))
                ]
            )
            page.dialog = dlg
            dlg.open = True
            page.update()

        refresh_categories_display()

        page.add(
            ft.Row([title_text,
                    ft.IconButton(ft.icons.SETTINGS, on_click=lambda e: show_setup_view(), tooltip="تغيير الإعدادات")],
                   alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            balance_text,

            # --- زر التحديث السحابي بجانب حالة الاتصال ---
            ft.Row([status_text,
                    ft.IconButton(ft.icons.REFRESH, tooltip="تحديث البيانات من السحابة", on_click=sync_from_cloud,
                                  icon_color=ft.colors.GREEN_400)], alignment=ft.MainAxisAlignment.CENTER),

            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("توزيع الميزانية الحالي:", color=ft.colors.GREY_400, size=16),
                        ft.IconButton(icon=ft.icons.SYNC_ALT, icon_color=ft.colors.PURPLE_400,
                                      tooltip="مناقلة بين الأقسام", on_click=open_transfer_dialog)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    categories_display
                ]),
                padding=10, border=ft.border.all(1, ft.colors.GREY_800), border_radius=10
            ),

            ft.Divider(height=20, color=ft.colors.GREY_800),
            deposit_section,

            ft.Divider(height=20, color=ft.colors.GREY_800),
            ft.Text("تسجيل مصروف:", size=18, color=ft.colors.GREY_400),
            ft.Row([item_name_input, item_price_input, item_category_dropdown], alignment=ft.MainAxisAlignment.CENTER),
            ft.ElevatedButton("سحب من الرصيد ورفع للسحابة", on_click=record_expense, bgcolor=ft.colors.RED_700,
                              color=ft.colors.WHITE, width=350, icon=ft.icons.CLOUD_UPLOAD, height=45),

            ft.Divider(height=20, color=ft.colors.GREY_800),
            ft.OutlinedButton("سجل المصاريف وتعديلها", on_click=show_history, icon=ft.icons.HISTORY, width=350,
                              height=45),
            ft.TextButton("إعادة ضبط المصنع (حذف سحابي)", on_click=confirm_reset, icon=ft.icons.RESTART_ALT,
                          icon_color=ft.colors.RED),

            ft.Container(height=10)
        )

    if data['settings']['is_setup_done']:
        show_main_view()
    else:
        show_setup_view()


ft.app(target=main)
