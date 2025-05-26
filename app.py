from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, SelectField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Regexp, Email, Length, Optional, URL
from flask_caching import Cache
import os
import logging
from datetime import date, datetime

# Importa a função calculate_amortization do módulo loan_simulation
from loan_simulation import calculate_amortization

# --- Configuração de Logging ---
# Configura o logger para exibir mensagens INFO ou superiores, com formato detalhado.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# --- Configuração do Aplicativo ---
class Config:
    """Configuração base para o aplicativo Flask."""
    # URI do banco de dados, prioriza variável de ambiente 'DATABASE_URL' ou usa SQLite local.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Desativa o rastreamento de modificações do SQLAlchemy para economizar memória.
    # Chave secreta para segurança de sessões e CSRF. Obtém da variável de ambiente ou gera uma aleatória.
    SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(32))
    CACHE_TYPE = 'SimpleCache'  # Tipo de cache a ser usado (cache em memória simples).
    CACHE_DEFAULT_TIMEOUT = 300  # Tempo de expiração padrão para itens em cache (5 minutos).


class DevelopmentConfig(Config):
    """Configurações específicas para o ambiente de desenvolvimento."""
    DEBUG = True  # Ativa o modo de depuração (recarregamento automático, depurador interativo).
    ENV = 'development'  # Define o ambiente como desenvolvimento.
    # SQLALCHEMY_ECHO = True # Descomente para ver todas as queries SQL geradas pelo SQLAlchemy.


class ProductionConfig(Config):
    """Configurações específicas para o ambiente de produção."""
    DEBUG = False  # Desativa o modo de depuração em produção para segurança e performance.
    ENV = 'production'  # Define o ambiente como produção.
    # Para produção, DATABASE_URL deve ser uma string de conexão para um banco de dados persistente.
    # Ex: app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL_PROD')


# --- Inicialização do Flask e Extensões ---
app = Flask(__name__)
# Carrega a configuração. Pode ser alterado para ProductionConfig em um ambiente de produção.
app.config.from_object(DevelopmentConfig)

db = SQLAlchemy(app)
cache = Cache(app)


# --- Modelos de Banco de Dados ---
class FinanceCompany(db.Model):
    """
    Modelo de banco de dados para representar uma instituição financeira.
    Atributos:
        id (int): Chave primária.
        name (str): Nome da financeira (único).
        code (str): Código da financeira (único).
        basic_interest_rate (float): Taxa de juros básica anual em porcentagem.
        last_updated (date): Data da última atualização dos dados da financeira.
        # Novos campos para contato e localização
        cnpj (str): CNPJ da financeira (único). # Added CNPJ field
        country (str): País de origem da financeira.
        address_street (str): Rua/Avenida.
        address_number (str): Número do endereço.
        address_complement (str): Complemento do endereço (opcional).
        address_neighborhood (str): Bairro.
        address_city (str): Cidade.
        address_state (str): Estado/Província.
        address_zipcode (str): CEP / Código Postal.
        contact_phone (str): Telefone de contato.
        contact_email (str): Email de contato.
        website_url (str): URL do website.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)
    basic_interest_rate = db.Column(db.Float, nullable=False)
    last_updated = db.Column(db.Date, nullable=False, default=date.today)
    cnpj = db.Column(db.String(18), unique=True, nullable=False) # Added CNPJ column
    country = db.Column(db.String(50), nullable=True) # Alterado para nullable=True para campos opcionais
    address_street = db.Column(db.String(200), nullable=True)
    address_number = db.Column(db.String(20), nullable=True)
    address_complement = db.Column(db.String(100), nullable=True)
    address_neighborhood = db.Column(db.String(100), nullable=True)
    address_city = db.Column(db.String(100), nullable=True)
    address_state = db.Column(db.String(50), nullable=True)
    address_zipcode = db.Column(db.String(20), nullable=True)
    contact_phone = db.Column(db.String(50), nullable=True)
    contact_email = db.Column(db.String(120), nullable=True)
    website_url = db.Column(db.String(200), nullable=True)


    def __repr__(self):
        """Representação em string do objeto FinanceCompany."""
        return f"<FinanceCompany {self.name} - {self.code}>"

    def to_dict(self):
        """Converte o objeto do modelo em um dicionário."""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'basic_interest_rate': self.basic_interest_rate,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'cnpj': self.cnpj, # Added CNPJ to to_dict method
            'country': self.country,
            'address_street': self.address_street,
            'address_number': self.address_number,
            'address_complement': self.address_complement,
            'address_neighborhood': self.address_neighborhood,
            'address_city': self.address_city,
            'address_state': self.address_state,
            'address_zipcode': self.address_zipcode,
            'contact_phone': self.contact_phone,
            'contact_email': self.contact_email,
            'website_url': self.website_url
        }


# --- Formulários WTForms ---
class LoanSimulationForm(FlaskForm):
    """Formulário para simulação de empréstimos."""
    company = SelectField('Financeira', coerce=int, validators=[DataRequired(message="Selecione uma financeira.")])
    principal = FloatField('Valor do Empréstimo (R$)', validators=[
        DataRequired(message="O valor do empréstimo é obrigatório."),
        NumberRange(min=100, max=1000000, message="O valor deve ser entre R$100 e R$1.000.000.")
    ])
    years = IntegerField('Prazo (anos)', validators=[
        DataRequired(message="O prazo em anos é obrigatório."),
        NumberRange(min=1, max=30, message="O prazo deve ser entre 1 e 30 anos.")
    ])
    extra_amortization = FloatField('Amortização Extra (R$ - opcional)', validators=[
        Optional(),  # Campo opcional
        NumberRange(min=0, message="A amortização extra não pode ser negativa.")
    ], default=0.00)


class AddCompanyForm(FlaskForm):
    """Formulário para adicionar uma nova instituição financeira."""
    name = StringField('Nome da Financeira', validators=[
        DataRequired(message="O nome é obrigatório."),
        Length(min=2, max=100, message="O nome deve ter entre 2 e 100 caracteres."),
        Regexp(r'^[a-zA-Z0-9\sà-úÀ-Ú.-]+$',
               message="O nome contém caracteres inválidos. Use letras, números, espaços, hífens e pontos.")
    ])
    cnpj = StringField('CNPJ', validators=[ # Added CNPJ field
        DataRequired(message="O CNPJ é obrigatório."),
        Length(min=14, max=18, message="O CNPJ deve ter 14 ou 18 caracteres (incluindo formatação)."),
        Regexp(r'^\d{2}\.\d{3}\.\d{3}\/\d{4}\-\d{2}$',
               message="Formato de CNPJ inválido. Use XX.XXX.XXX/XXXX-XX.")
    ])
    code = StringField('Código', validators=[
        DataRequired(message="O código é obrigatório."),
        Length(min=3, max=10, message="O código deve ter entre 3 e 10 caracteres."),
        Regexp(r'^[A-Z0-9]{3,10}$', message="O código deve ter entre 3 e 10 caracteres alfanuméricos maiúsculos.")
    ])
    basic_interest_rate = FloatField('Taxa de Juros Anual (%)', validators=[
        DataRequired(message="A taxa de juros é obrigatória."),
        NumberRange(min=0.1, max=100, message="A taxa deve ser entre 0.1% e 100%.")
    ])
    # Novos campos adicionados para corresponder ao HTML
    country = SelectField('País de Origem', choices=[
        ('', '-- Selecione o País --'),
        ('Brasil', 'Brasil'),
        ('Portugal', 'Portugal'),
        ('Estados Unidos', 'Estados Unidos'),
        ('Canada', 'Canadá'),
        ('Alemanha', 'Alemanha'),
        ('Espanha', 'Espanha'),
        ('Franca', 'França'),
        ('Japao', 'Japão'),
        ('Reino Unido', 'Reino Unido')
    ], validators=[DataRequired(message="O país de origem é obrigatório.")])
    address_street = StringField('Rua/Avenida', validators=[Optional(), Length(max=200)])
    address_number = StringField('Número', validators=[Optional(), Length(max=20)])
    address_complement = StringField('Complemento', validators=[Optional(), Length(max=100)])
    address_neighborhood = StringField('Bairro', validators=[Optional(), Length(max=100)])
    address_city = StringField('Cidade', validators=[Optional(), Length(max=100)])
    address_state = StringField('Estado/Província', validators=[Optional(), Length(max=50)])
    address_zipcode = StringField('CEP / Código Postal', validators=[Optional(), Length(max=20)])
    contact_phone = StringField('Telefone de Contato', validators=[Optional(), Length(max=50)])
    contact_email = StringField('Email de Contato', validators=[Optional(), Email(), Length(max=120)])
    website_url = StringField('Website', validators=[Optional(), URL(), Length(max=200)])


class ContactForm(FlaskForm):
    """Formulário de contato."""
    name = StringField('Nome', validators=[
        DataRequired(message="O nome é obrigatório."),
        Length(min=2, max=100, message="O nome deve ter entre 2 e 100 caracteres.")
    ])
    email = StringField('E-mail', validators=[
        DataRequired(message="O e-mail é obrigatório."),
        Email(message="Insira um e-mail válido.")
    ])
    message = TextAreaField('Mensagem', validators=[
        DataRequired(message="A mensagem é obrigatória."),
        Length(min=10, max=500, message="A mensagem deve ter entre 10 e 500 caracteres.")
    ])


# --- Funções Utilitárias ---
# A função calculate_amortization foi movida para loan_simulation.py

# Filtros Jinja Personalizados
@app.template_filter('calculate_pre_approved')
def calculate_pre_approved(interest_rate):
    """
    Estima um valor pré-aprovado com base na taxa de juros.
    Quanto menor a taxa, maior o valor pré-aprovado (dentro de limites).
    """
    try:
        # Baseado em uma lógica simples de que taxas mais baixas permitem valores maiores
        # Assegura que o valor esteja entre 10.000 e 500.000
        pre_approved_amount = 500000 - (interest_rate * 5000)  # Ajuste o multiplicador conforme a necessidade
        return max(10000, min(pre_approved_amount, 500000))
    except (TypeError, ValueError) as e:
        logger.error(f"Erro ao calcular valor pré-aprovado para taxa {interest_rate}: {e}")
        return 10000  # Retorna um valor padrão em caso de erro


@app.template_filter('dateformat')
def dateformat(d):
    """Formata a data como DD/MM/YYYY. Retorna string vazia se a data for None."""
    if d:
        return d.strftime('%d/%m/%Y')
    return ""


@app.context_processor
def inject_global_data():
    """Injeta dados globais como o ano atual em todos os templates."""
    return dict(current_year=datetime.now().year)


# --- Tratadores de Erro ---
@app.errorhandler(404)
def page_not_found(e):
    """Handler para erros 404 (Página Não Encontrada)."""
    flash("Página não encontrada.", 'error')
    logger.warning(f"404 Not Found: {request.url}")  # Log mais detalhado para 404
    return render_template('error.html', error_code=404, error_message="Página não encontrada"), 404


@app.errorhandler(500)
def internal_server_error(e):
    """Handler para erros 500 (Erro Interno do Servidor)."""
    flash("Ocorreu um erro interno no servidor.", 'error')
    logger.exception("500 Internal Server Error Caught")  # Usa exception para logar o traceback completo
    return render_template('error.html', error_code=500, error_message="Erro interno do servidor"), 500


# --- Rotas do Aplicativo ---
@app.route('/')
@cache.cached(timeout=60, query_string=True)  # Cache de 1 minuto para a página inicial
def index():
    """Rota da página inicial."""
    logger.info("Acessando rota index")
    sort_by = request.args.get('sort', 'name')  # Parâmetro de query para ordenação
    if sort_by == 'rate':
        companies = FinanceCompany.query.order_by(FinanceCompany.basic_interest_rate.asc()).all()
    else:
        companies = FinanceCompany.query.order_by(FinanceCompany.name.asc()).all()
    return render_template('index.html', companies=companies, sort_by=sort_by)


@app.route('/loan_simulation', methods=['GET', 'POST'])
def loan_simulation():
    """Rota para a página de simulação de empréstimo."""
    logger.info("Acessando rota loan_simulation")
    form = LoanSimulationForm()
    companies = FinanceCompany.query.all()
    form.company.choices = [(c.id, c.name) for c in companies]  # Popula as opções da financeira

    schedule = None
    summary = None
    # Variáveis para repopular o formulário e manter o estado da simulação
    principal_value = ''
    years_value = ''
    selected_company_id = None
    extra_amortization_value = '0.00'

    if form.validate_on_submit():
        try:
            company = FinanceCompany.query.get(form.company.data)
            if not company:
                flash("Financeira selecionada não encontrada.", 'error')
            else:
                # Armazena os valores para repopular o formulário
                principal_value = f"{form.principal.data:.2f}"
                years_value = str(form.years.data)
                selected_company_id = form.company.data
                extra_amortization_value = f"{form.extra_amortization.data:.2f}"

                # Calcula a amortização usando a função utilitária importada
                schedule, total_interest, total_principal_paid, total_paid = calculate_amortization(
                    principal_value=form.principal.data,
                    annual_interest_rate=company.basic_interest_rate,
                    years_value=form.years.data,
                    extra_amortization_value=form.extra_amortization.data
                )
                summary = {
                    "principal": f"{form.principal.data:.2f}",
                    "total_interest": f"{total_interest:.2f}",
                    "total_principal": f"{total_principal_paid:.2f}",
                    "total_paid": f"{total_paid:.2f}"
                }
                flash('Simulação calculada com sucesso!', 'success')
                logger.info(
                    f"Simulação de empréstimo concluída: Principal={form.principal.data}, Anos={form.years.data}, Empresa={company.name}")
        except ValueError as ve:
            # Captura erros de validação da função calculate_amortization
            flash(f"Erro de validação: {str(ve)}", 'error')
            logger.error(f"Erro de validação na simulação: {ve}")
        except Exception as e:
            # Captura outros erros inesperados durante o cálculo
            flash(f"Erro ao calcular a simulação: {str(e)}", 'error')
            logger.error(f"Erro inesperado na simulação de empréstimo: {e}", exc_info=True)
    elif request.method == 'POST':  # Formulário submetido, mas não validou (erros de validação do WTForms)
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Erro no campo '{getattr(form, field).label.text}': {error}", 'error')
        # Tenta preservar os valores inseridos pelo usuário, mesmo com erro de validação
        principal_value = request.form.get('principal', '')
        years_value = request.form.get('years', '')
        selected_company_id = request.form.get('company', None)
        extra_amortization_value = request.form.get('extra_amortization', '0.00')

    return render_template(
        'loan_simulation.html',
        form=form,
        companies=companies,
        schedule=schedule,
        summary=summary,
        principal_value=principal_value,
        years_value=years_value,
        selected_company_id=selected_company_id,
        extra_amortization_value=extra_amortization_value
    )


@app.route('/add_company', methods=['GET', 'POST'])
def add_company():
    """Rota para adicionar uma nova instituição financeira."""
    logger.info("Acessando rota add_company")
    form = AddCompanyForm()
    if form.validate_on_submit():
        try:
            # Verifica se já existe uma financeira com o mesmo código ou CNPJ
            existing_company_code = FinanceCompany.query.filter_by(code=form.code.data.strip()).first()
            existing_company_cnpj = FinanceCompany.query.filter_by(cnpj=form.cnpj.data.strip()).first() # Check for existing CNPJ
            if existing_company_code:
                flash(f"Uma financeira com o código '{form.code.data.strip()}' já existe.", 'error')
                logger.warning(f"Tentativa de adicionar empresa com código duplicado: {form.code.data.strip()}")
            elif existing_company_cnpj: # New condition
                flash(f"Uma financeira com o CNPJ '{form.cnpj.data.strip()}' já existe.", 'error') # New flash message
                logger.warning(f"Tentativa de adicionar empresa com CNPJ duplicado: {form.cnpj.data.strip()}") # New log
            else:
                new_company = FinanceCompany(
                    name=form.name.data.strip(),
                    cnpj=form.cnpj.data.strip(), # Added CNPJ field
                    code=form.code.data.strip(),
                    basic_interest_rate=form.basic_interest_rate.data,
                    last_updated=date.today(),
                    # Novos campos
                    country=form.country.data,
                    address_street=form.address_street.data,
                    address_number=form.address_number.data,
                    address_complement=form.address_complement.data,
                    address_neighborhood=form.address_neighborhood.data,
                    address_city=form.address_city.data,
                    address_state=form.address_state.data,
                    address_zipcode=form.address_zipcode.data,
                    contact_phone=form.contact_phone.data,
                    contact_email=form.contact_email.data,
                    website_url=form.website_url.data
                )
                db.session.add(new_company)
                db.session.commit()  # Salva no banco de dados
                flash('Financeira adicionada com sucesso!', 'success')
                logger.info(f"Nova empresa adicionada: {form.name.data}")
                return redirect(url_for('loan_simulation'))  # Redireciona para evitar re-envio do formulário
        except Exception as e:
            db.session.rollback()  # Desfaz alterações no banco em caso de erro
            flash(f"Erro ao adicionar a financeira: {str(e)}", 'error')
            logger.error(f"Erro ao adicionar empresa: {e}", exc_info=True)
    elif request.method == 'POST':  # Formulário submetido, mas não validou (erros de validação do WTForms)
        logger.warning("Formulário de adição de empresa não validou.")
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Erro no campo '{getattr(form, field).label.text}': {error}", 'error')
                logger.warning(f"Erro de validação no campo '{field}': {error}")
    return render_template('add_company.html', form=form)


@app.route('/company/<int:id>')
def company_details(id):
    """Exibe detalhes de uma instituição financeira específica."""
    logger.info(f"Acessando rota company_details para ID {id}")
    # Busca a empresa pelo ID ou retorna 404 se não encontrada
    company = FinanceCompany.query.get_or_404(id)
    return render_template('company_details.html', company=company)


@app.route('/terms')
@cache.cached(timeout=3600)  # Cache de 1 hora para páginas estáticas
def terms():
    """Página de Termos de Uso."""
    logger.info("Acessando rota terms")
    return render_template('terms.html')


@app.route('/privacy')
@cache.cached(timeout=3600)  # Cache de 1 hora para páginas estáticas
def privacy():
    """Página de Política de Privacidade."""
    logger.info("Acessando rota privacy")
    return render_template('privacy.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Página de Contato com formulário."""
    logger.info("Acessando rota contact")
    form = ContactForm()
    if form.validate_on_submit():
        try:
            # Lógica para enviar e-mail (simulada aqui, substituir por um serviço de e-mail real)
            contact_data = {
                "name": form.name.data,
                "email": form.email.data,
                "message": form.message.data
            }
            logger.info(f"Formulário de contato submetido: {contact_data}")
            flash("Mensagem enviada com sucesso! Entraremos em contato em breve.", 'success')
            return redirect(url_for('contact'))  # Redireciona para evitar re-envio
        except Exception as e:
            flash(f"Erro ao enviar a mensagem: {str(e)}", 'error')
            logger.error(f"Erro ao processar formulário de contato: {e}", exc_info=True)
    elif request.method == 'POST':  # Formulário submetido, mas não validou (erros de validação do WTForms)
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Erro no campo '{getattr(form, field).label.text}': {error}", 'error')
    return render_template('contact.html', form=form)


# --- Execução do Aplicativo ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Cria as tabelas do banco de dados se ainda não existirem

        # Adiciona instituições financeiras de exemplo se o banco estiver vazio
        if not FinanceCompany.query.first():
            logger.info("Adicionando instituições financeiras de exemplo...")
            companies_data = [
                FinanceCompany(name="Banco Alpha", code="BA001", basic_interest_rate=1.2, last_updated=date.today(),
                               cnpj="01.234.567/0001-89", # Added CNPJ for example data
                               country="Brasil", address_street="Rua A", address_number="123",
                               address_neighborhood="Centro", address_city="São Paulo", address_state="SP",
                               address_zipcode="01000-000", contact_phone="+5511987654321",
                               contact_email="contato@alpha.com", website_url="https://www.bancoalpha.com"),
                FinanceCompany(name="CrediBeta", code="CB002", basic_interest_rate=1.5, last_updated=date.today(),
                               cnpj="98.765.432/0001-21", # Added CNPJ for example data
                               country="Brasil", address_street="Av. B", address_number="456",
                               address_neighborhood="Jardins", address_city="Rio de Janeiro", address_state="RJ",
                               address_zipcode="20000-000", contact_phone="+5521912345678",
                               contact_email="contato@credibeta.com", website_url="https://www.credibeta.com"),
                FinanceCompany(name="FinanGamma", code="FG003", basic_interest_rate=1.0, last_updated=date.today(),
                               cnpj="11.222.333/0001-44", # Added CNPJ for example data
                               country="Brasil", address_street="Rua C", address_number="789",
                               address_neighborhood="Savassi", address_city="Belo Horizonte", address_state="MG",
                               address_zipcode="30000-000", contact_phone="+5531998765432",
                               contact_email="contato@fingamma.com", website_url="https://www.finangamma.com"),
                FinanceCompany(name="Empréstimos Delta", code="ED004", basic_interest_rate=1.8,
                               last_updated=date.today(),
                               cnpj="44.555.666/0001-77", # Added CNPJ for example data
                               country="Brasil", address_street="Av. D",
                               address_number="101", address_neighborhood="Asa Sul", address_city="Brasília",
                               address_state="DF", address_zipcode="70000-000", contact_phone="+5561954321098",
                               contact_email="contato@delta.com", website_url="https://www.emprestimosdelta.com")
            ]
            db.session.add_all(companies_data)
            db.session.commit()
            logger.info("Empresas de exemplo adicionadas com sucesso.")

    app.run(debug=True, host='0.0.0.0', port=5000)  # Roda o aplicativo em modo debug, acessível externamente.