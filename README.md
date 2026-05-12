# BibliotecaPI - Sistema de Gerenciamento de Biblioteca

Este é um sistema desenvolvido em Django para o gerenciamento completo de uma biblioteca, incluindo controle de acervo, catálogo, circulação (empréstimos e reservas), e importação de dados em lote.

## Funcionalidades Principais

-   **Catálogo:** Cadastro e consulta de livros, autores, editoras e categorias, com suporte a ISBN-10 e ISBN-13.
-   **Acervo:** Gestão de exemplares físicos, controle de status (Disponível, Emprestado) e geração automática de número de tombo.
-   **Circulação:** Registro de empréstimos, devoluções (com cálculo de multa por atraso) e reservas de livros.
-   **Importação:** Importação de livros e exemplares em lote via arquivo CSV.
-   **Usuários:** Sistema de permissões com diferentes perfis (Admin, Bibliotecário, Leitor).

## Passo a Passo para Executar o Projeto Localmente

Para rodar o projeto localmente, siga os passos abaixo:

### Pré-requisitos

-   Python 3.8+ instalado.
-   Git instalado.
-   Ambiente virtual configurado (recomendado).

### 1. Clonar o Repositório

Se você ainda não clonou o repositório, abra o terminal e execute:

```bash
git clone https://github.com/SEU_USUARIO/pi_grupo_11.git
cd "pi grupo 11"
```

### 2. Configurar o Ambiente Virtual

Crie e ative um ambiente virtual para isolar as dependências do projeto.

No Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

No Linux/macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependências

Com o ambiente virtual ativado, instale os pacotes necessários que estão listados no arquivo `requirements.txt`:

```bash
pip install -r BibliotecaPI/requirements.txt
```

### 4. Configurar as Variáveis de Ambiente

O projeto utiliza variáveis de ambiente para configurações sensíveis. Crie um arquivo `.env` na raiz do projeto (mesmo nível da pasta `BibliotecaPI`) ou dentro da pasta `BibliotecaPI` baseando-se no `.env.example` se existir, ou configure as variáveis necessárias de acordo com o `settings.py`. Como este é um ambiente de desenvolvimento local, muitas configurações podem já estar padronizadas no `settings.py`.

### 5. Executar as Migrações do Banco de Dados

Antes de iniciar o servidor, é necessário criar as tabelas no banco de dados SQLite padrão:

```bash
cd BibliotecaPI
python manage.py makemigrations
python manage.py migrate
```

### 6. Criar um Superusuário (Administrador)

Para acessar o painel de administração e testar todas as funcionalidades (como importação e cadastro de livros), crie um usuário administrador:

```bash
python manage.py createsuperuser
```
Siga os prompts para definir o nome de usuário, e-mail e senha.

### 7. Iniciar o Servidor de Desenvolvimento

Agora você pode iniciar o servidor local:

```bash
python manage.py runserver
```

### 8. Acessar o Sistema

Abra o seu navegador e acesse:

-   Página Inicial do Sistema: `http://127.0.0.1:8000/`
-   Painel de Administração do Django: `http://127.0.0.1:8000/admin/`

Faça o login com o superusuário que você criou no passo 6.

## Verificando as Novas Alterações

Após acessar o sistema, você pode verificar as recentes melhorias:

1.  **Guia Catálogo:**
    -   Vá em "Catálogo" e clique em "Novo livro". Verifique os campos de "Quantidade de Exemplares", "ISBN-10" e "ISBN-13".
    -   No formulário, observe os novos botões para cadastrar "Novo Autor", "Nova Editora" e "Nova Categoria" dinamicamente.
    -   Teste a busca nos campos de seleção (dropdowns com Select2).
    -   Na lista de livros, veja o botão "Cadastrar Exemplar" para adicionar rapidamente mais cópias.

2.  **Guia Reservas:**
    -   Vá em "Circulação" > "Reservas" e clique em "Nova Reserva".
    -   Teste o novo formulário de busca para encontrar livros por palavra-chave, autor ou ISBN antes de realizar a reserva.

3.  **Guia Exemplares e Empréstimos:**
    -   Acesse as respectivas guias e teste os novos campos de busca para filtrar rapidamente as informações desejadas (por título ou tombo).
