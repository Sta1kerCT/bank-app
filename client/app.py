import requests
import click
import json
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import time
import sys

console = Console()
BASE_URL = "http://server:8000"  # В Docker Compose


# Для локального тестирования: "http://localhost:8000"

class BankClient:
    def __init__(self, base_url=None):
        self.base_url = base_url or BASE_URL
        self.session = requests.Session()

    def create_account(self, owner_name, initial_balance=0):
        """Создать новый счет"""
        url = f"{self.base_url}/accounts/"
        data = {
            "owner_name": owner_name,
            "initial_balance": float(initial_balance)
        }

        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
        ) as progress:
            task = progress.add_task("Создание счета...", total=1)
            response = self.session.post(url, json=data)
            progress.update(task, completed=1)

        if response.status_code == 201:
            account = response.json()
            console.print(f"[green]✓ Счет создан успешно![/green]")
            console.print(f"Номер счета: [bold]{account['account_number']}[/bold]")
            console.print(f"Владелец: {account['owner_name']}")
            console.print(f"Баланс: ${account['balance']:.2f}")
            return account
        else:
            console.print(f"[red]Ошибка: {response.json().get('detail', 'Unknown error')}[/red]")
            return None

    def get_account(self, account_number):
        """Получить информацию о счете"""
        url = f"{self.base_url}/accounts/{account_number}"
        response = self.session.get(url)

        if response.status_code == 200:
            account = response.json()

            table = Table(title=f"Счет #{account['account_number']}")
            table.add_column("Поле", style="cyan")
            table.add_column("Значение", style="magenta")

            table.add_row("ID", str(account['id']))
            table.add_row("Номер счета", account['account_number'])
            table.add_row("Владелец", account['owner_name'])
            table.add_row("Баланс", f"${account['balance']:.2f}")
            table.add_row("Статус", "Активен" if account['is_active'] else "Неактивен")
            table.add_row("Создан", account['created_at'])

            console.print(table)
            return account
        else:
            console.print(f"[red]Счет не найден[/red]")
            return None

    def list_accounts(self, limit=10):
        """Показать список счетов"""
        url = f"{self.base_url}/accounts/?limit={limit}"
        response = self.session.get(url)

        if response.status_code == 200:
            accounts = response.json()

            table = Table(title=f"Счета (всего: {len(accounts)})")
            table.add_column("Номер счета", style="cyan")
            table.add_column("Владелец", style="green")
            table.add_column("Баланс", style="yellow", justify="right")
            table.add_column("Статус", style="magenta")

            for account in accounts:
                status = "✅" if account['is_active'] else "❌"
                table.add_row(
                    account['account_number'],
                    account['owner_name'],
                    f"${account['balance']:.2f}",
                    status
                )

            console.print(table)
            return accounts
        else:
            console.print(f"[red]Ошибка при получении списка счетов[/red]")
            return None

    def deposit(self, to_account, amount):
        """Пополнить счет"""
        url = f"{self.base_url}/transactions/"
        data = {
            "to_account": to_account,
            "amount": float(amount),
            "transaction_type": "DEPOSIT"
        }

        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
        ) as progress:
            task = progress.add_task("Инициализация депозита...", total=1)
            response = self.session.post(url, json=data)
            progress.update(task, completed=1)

        if response.status_code == 202:
            transaction = response.json()
            console.print(f"[green]✓ Депозит инициализирован![/green]")
            console.print(f"ID транзакции: [bold]{transaction['id']}[/bold]")
            console.print(f"Сумма: ${amount}")
            console.print(f"Статус: {transaction['status']}")

            self._track_transaction(transaction['id'])
            return transaction
        else:
            console.print(f"[red]Ошибка: {response.json().get('detail', 'Unknown error')}[/red]")
            return None

    def withdraw(self, from_account, amount):
        """Снять средства"""
        url = f"{self.base_url}/transactions/"
        data = {
            "from_account": from_account,
            "to_account": from_account,
            "amount": float(amount),
            "transaction_type": "WITHDRAW"
        }

        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
        ) as progress:
            task = progress.add_task("Инициализация снятия...", total=1)
            response = self.session.post(url, json=data)
            progress.update(task, completed=1)

        if response.status_code == 202:
            transaction = response.json()
            console.print(f"[green]✓ Снятие инициализировано![/green]")
            console.print(f"ID транзакции: [bold]{transaction['id']}[/bold]")
            console.print(f"Сумма: ${amount}")
            console.print(f"Статус: {transaction['status']}")

            self._track_transaction(transaction['id'])
            return transaction
        else:
            console.print(f"[red]Ошибка: {response.json().get('detail', 'Unknown error')}[/red]")
            return None

    def transfer(self, from_account, to_account, amount):
        """Перевести средства между счетами"""
        url = f"{self.base_url}/transactions/"
        data = {
            "from_account": from_account,
            "to_account": to_account,
            "amount": float(amount),
            "transaction_type": "TRANSFER"
        }

        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
        ) as progress:
            task = progress.add_task("Инициализация перевода...", total=1)
            response = self.session.post(url, json=data)
            progress.update(task, completed=1)

        if response.status_code == 202:
            transaction = response.json()
            console.print(f"[green]✓ Перевод инициализирован![/green]")
            console.print(f"ID транзакции: [bold]{transaction['id']}[/bold]")
            console.print(f"С отчета: {from_account}")
            console.print(f"На счет: {to_account}")
            console.print(f"Сумма: ${amount}")
            console.print(f"Статус: {transaction['status']}")

            self._track_transaction(transaction['id'])
            return transaction
        else:
            console.print(f"[red]Ошибка: {response.json().get('detail', 'Unknown error')}[/red]")
            return None

    def _track_transaction(self, transaction_id, max_attempts=10):
        """Отслеживать статус транзакции"""
        url = f"{self.base_url}/transactions/{transaction_id}"

        console.print("\n[yellow]Отслеживание статуса транзакции...[/yellow]")

        with Progress() as progress:
            task = progress.add_task("Ожидание обработки...", total=max_attempts)

            for i in range(max_attempts):
                time.sleep(1)
                response = self.session.get(url)

                if response.status_code == 200:
                    transaction = response.json()
                    status = transaction['status']

                    if status == "COMPLETED":
                        progress.update(task, completed=max_attempts)
                        console.print(f"[green]✓ Транзакция успешно выполнена![/green]")
                        break
                    elif status == "FAILED":
                        progress.update(task, completed=max_attempts)
                        console.print(f"[red]✗ Транзакция не удалась[/red]")
                        break
                    elif status == "PROCESSING":
                        progress.update(task, completed=i + 1)

                if i == max_attempts - 1:
                    console.print(f"[yellow]Транзакция все еще в обработке...[/yellow]")

    def get_transaction(self, transaction_id):
        """Получить информацию о транзакции"""
        url = f"{self.base_url}/transactions/{transaction_id}"
        response = self.session.get(url)

        if response.status_code == 200:
            transaction = response.json()

            table = Table(title=f"Транзакция #{transaction['id']}")
            table.add_column("Поле", style="cyan")
            table.add_column("Значение", style="magenta")

            table.add_row("ID", str(transaction['id']))
            table.add_row("От счета", transaction.get('from_account', 'N/A'))
            table.add_row("На счет", transaction['to_account'])
            table.add_row("Сумма", f"${transaction['amount']:.2f}")
            table.add_row("Тип", transaction['transaction_type'])
            table.add_row("Статус", transaction['status'])
            table.add_row("Создана", transaction['created_at'])

            console.print(table)
            return transaction
        else:
            console.print(f"[red]Транзакция не найдена[/red]")
            return None

    def get_metrics(self):
        """Получить метрики Prometheus"""
        url = f"{self.base_url}/metrics"
        response = self.session.get(url)

        if response.status_code == 200:
            console.print("[bold]Метрики системы:[/bold]")
            console.print(response.text[:1000] + "..." if len(response.text) > 1000 else response.text)
            return response.text
        else:
            console.print(f"[red]Не удалось получить метрики[/red]")
            return None

    def health_check(self):
        """Проверить здоровье системы"""
        url = f"{self.base_url}/health"
        response = self.session.get(url)

        if response.status_code == 200:
            console.print(f"[green]✓ Система работает нормально[/green]")
            return True
        else:
            console.print(f"[red]✗ Проблемы с системой[/red]")
            return False


@click.group()
@click.option('--url', default=None, help='URL сервера')
@click.pass_context
def cli(ctx, url):
    """Банковский клиент - управление счетами и транзакциями"""
    ctx.ensure_object(dict)
    ctx.obj['client'] = BankClient(url)


@cli.command()
@click.option('--name', prompt='Имя владельца', help='Имя владельца счета')
@click.option('--balance', default=0.0, help='Начальный баланс')
@click.pass_context
def create(ctx, name, balance):
    """Создать новый счет"""
    ctx.obj['client'].create_account(name, balance)


@cli.command()
@click.argument('account_number')
@click.pass_context
def info(ctx, account_number):
    """Получить информацию о счете"""
    ctx.obj['client'].get_account(account_number)


@cli.command()
@click.option('--limit', default=10, help='Количество счетов для отображения')
@click.pass_context
def list(ctx, limit):
    """Показать список счетов"""
    ctx.obj['client'].list_accounts(limit)


@cli.command()
@click.argument('account_number')
@click.argument('amount', type=float)
@click.pass_context
def deposit(ctx, account_number, amount):
    """Пополнить счет"""
    ctx.obj['client'].deposit(account_number, amount)


@cli.command()
@click.argument('account_number')
@click.argument('amount', type=float)
@click.pass_context
def withdraw(ctx, account_number, amount):
    """Снять средства со счета"""
    ctx.obj['client'].withdraw(account_number, amount)


@cli.command()
@click.argument('from_account')
@click.argument('to_account')
@click.argument('amount', type=float)
@click.pass_context
def transfer(ctx, from_account, to_account, amount):
    """Перевести средства между счетами"""
    ctx.obj['client'].transfer(from_account, to_account, amount)


@cli.command()
@click.argument('transaction_id', type=int)
@click.pass_context
def transaction(ctx, transaction_id):
    """Получить информацию о транзакции"""
    ctx.obj['client'].get_transaction(transaction_id)


@cli.command()
@click.pass_context
def metrics(ctx):
    """Показать метрики системы"""
    ctx.obj['client'].get_metrics()


@cli.command()
@click.pass_context
def health(ctx):
    """Проверить здоровье системы"""
    ctx.obj['client'].health_check()


@cli.command()
@click.pass_context
def demo(ctx):
    """Демонстрация работы системы"""
    client = ctx.obj['client']

    console.print("[bold cyan]Демонстрация банковской системы[/bold cyan]\n")

    # 1. Создание счетов
    console.print("[bold]1. Создание счетов:[/bold]")
    account1 = client.create_account("Иван Иванов", 1000)
    account2 = client.create_account("Петр Петров", 500)

    if not account1 or not account2:
        console.print("[red]Не удалось создать счета для демонстрации[/red]")
        return

    acc1_num = account1['account_number']
    acc2_num = account2['account_number']

    # 2. Показ счетов
    console.print(f"\n[bold]2. Созданные счета:[/bold]")
    client.get_account(acc1_num)
    client.get_account(acc2_num)

    # 3. Депозит
    console.print(f"\n[bold]3. Пополнение счета {acc1_num} на $200:[/bold]")
    deposit_tx = client.deposit(acc1_num, 200)

    # 4. Перевод
    console.print(f"\n[bold]4. Перевод $150 с {acc1_num} на {acc2_num}:[/bold]")
    transfer_tx = client.transfer(acc1_num, acc2_num, 150)

    # 5. Снятие
    console.print(f"\n[bold]5. Снятие $100 со счета {acc2_num}:[/bold]")
    withdraw_tx = client.withdraw(acc2_num, 100)

    # 6. Финальные балансы
    console.print(f"\n[bold]6. Финальные балансы:[/bold]")
    time.sleep(3)
    client.get_account(acc1_num)
    client.get_account(acc2_num)

    # 7. Метрики
    console.print(f"\n[bold]7. Метрики системы:[/bold]")
    client.get_metrics()


if __name__ == '__main__':
    cli(obj={})