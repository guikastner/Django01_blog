# Agents Guide - Django Blog

Este arquivo define a arquitetura inicial e as regras de trabalho para evoluir o projeto de blog em Django. A implementacao ainda nao deve ser executada automaticamente; primeiro vamos incrementar e validar este guia.

## Objetivo do projeto

Construir um blog em Django com:

1. Sistema de posts.
2. Banco de dados PostgreSQL.
3. Armazenamento de imagens em MinIO.
4. Sistema de comentarios usando Django.

## Base de documentacao

Usar a documentacao do Django como referencia principal via Context7:

- Biblioteca Context7: `/django/django`
- Topicos consultados inicialmente:
  - Models e relacionamentos para aplicacoes de blog.
  - Configuracao `DATABASES` com backend PostgreSQL.
  - `ImageField`, `FileField`, `MEDIA_URL`, `MEDIA_ROOT` e API de storage.
  - Forms para entrada de comentarios.

Decisoes arquiteturais devem preferir APIs nativas do Django antes de criar abstracoes proprias.

## Arquitetura proposta

### Apps Django

Estrutura inicial sugerida:

- `blog`: posts, categorias/tags futuras, imagens de capa, listagem e detalhe de posts.
- `comments`: comentarios associados aos posts, moderacao e formulario publico.

O comments deve ser feito em um app serparado

### Sistema de posts

Modelo inicial sugerido: `Post`.

Campos previstos:

- `title`: titulo do post.
- `slug`: URL amigavel e unica.
- `excerpt`: resumo curto opcional.
- `content`: corpo do post.
- `cover_image`: imagem de capa usando `ImageField`.
- `status`: rascunho ou publicado.
- `published_at`: data/hora de publicacao.
- `created_at`: data/hora de criacao.
- `updated_at`: data/hora de atualizacao.
- `author`: relacionamento com `settings.AUTH_USER_MODEL`.

Regras iniciais:

- Posts publicos devem listar apenas registros com `status = published`.
- URLs de detalhe devem usar `slug`.
- O admin deve permitir busca por titulo, filtro por status e pre-preenchimento de slug a partir do titulo.

Os posts devem ser editados com um editor WYSIWYG

### Sistema de comentarios

Modelo inicial sugerido: `Comment`.

Campos previstos:

- `post`: `ForeignKey` para `Post`, com `related_name="comments"`.
- `name`: nome do autor do comentario.
- `email`: email para contato ou moderacao; nao deve ser exibido publicamente.
- `body`: texto do comentario.
- `is_approved`: controle de moderacao.
- `created_at`: data/hora de criacao.
- `updated_at`: data/hora de atualizacao.

Regras iniciais:

- Comentarios publicos devem exibir apenas `is_approved = True`.
- Novos comentarios devem entrar como nao aprovados por padrao.
- O formulario publico deve validar os campos pelo sistema de forms do Django.
- O admin deve permitir aprovar, reprovar e filtrar comentarios.

### PostgreSQL

O banco principal deve usar o backend oficial do Django para PostgreSQL:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "...",
        "USER": "...",
        "PASSWORD": "...",
        "HOST": "...",
        "PORT": "5432",
    }
}
```

Regras iniciais:

- Credenciais devem vir de variaveis de ambiente, nunca hardcoded.
- Usar PostgreSQL tambem no ambiente de desenvolvimento se a meta for reduzir diferencas com producao.
- Migrations devem ser pequenas e revisaveis.

### MinIO para imagens

MinIO deve ser tratado como storage S3-compativel.

Abordagem prevista:

- Usar `ImageField` nos models.
- Usar um backend de storage compativel com S3, como `django-storages` com `boto3`.
- Configurar endpoint, bucket, credenciais e URL publica por variaveis de ambiente.

Configuracoes esperadas:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_STORAGE_BUCKET_NAME`
- `AWS_S3_ENDPOINT_URL`
- `AWS_S3_REGION_NAME`
- `AWS_S3_CUSTOM_DOMAIN` ou estrategia equivalente para URL publica

Regras iniciais:

- O banco deve armazenar apenas o caminho/identificador da imagem, nao o binario.
- Uploads devem ser organizados por pasta, por exemplo `posts/covers/%Y/%m/`.
- Validar formatos e tamanho maximo antes de aceitar upload publico.
- Em desenvolvimento, o MinIO deve ser inicializado por Docker Compose quando a execucao comecar.

### Views, URLs e templates

Fluxo publico inicial:

- Lista de posts publicados.
- Detalhe do post por slug.
- Formulario de comentario na pagina de detalhe.
- Confirmacao simples apos envio de comentario informando que ele aguarda aprovacao.

Preferencias:

- Usar class-based views quando reduzirem repeticao.
- Usar `QuerySet` explicito para filtrar posts publicados e comentarios aprovados.
- Evitar logica de negocio complexa em templates.

### Admin

O admin do Django sera a primeira interface editorial.

Configuracoes esperadas:

- `PostAdmin` com busca, filtros, ordenacao, `prepopulated_fields` para slug e campos de data somente leitura quando fizer sentido.
- `CommentAdmin` com filtros por aprovacao, post e data, alem de action para aprovar comentarios.

### Testes iniciais

Cobertura minima antes de considerar a primeira execucao pronta:

- Model tests para `Post.__str__`, slug/unicidade se customizado, status publicado.
- Query tests para garantir que somente posts publicados aparecem na listagem publica.
- Tests de comentarios para garantir que novos comentarios nao sao aprovados automaticamente.
- View tests para lista, detalhe e envio de comentario.

## Dependencias previstas

Dependencias Python provaveis:

- `Django`
- `psycopg` ou `psycopg2-binary`
- `django-storages`
- `boto3`
- `Pillow`
- `python-decouple` ou alternativa equivalente para configuracao por ambiente

Dependencias de infraestrutura provaveis:

- PostgreSQL
- MinIO
- Docker Compose para desenvolvimento local

## Ordem incremental sugerida

1. Validar este `agents.md`.
2. Criar o projeto Django base, se ainda nao existir.
3. Configurar variaveis de ambiente e settings por ambiente.
4. Adicionar PostgreSQL.
5. Criar app de posts.
6. Criar models, admin, urls, views e templates de posts.
7. Configurar MinIO e storage de imagens.
8. Criar sistema de comentarios.
9. Adicionar testes.
10. Revisar seguranca basica antes de qualquer deploy.

## Regras para proximos agentes

- Antes de editar codigo, ler este arquivo e confirmar o incremento pedido.
- Nao executar criacao de projeto, instalacao de dependencias ou migrations sem pedido explicito.
- Manter alteracoes pequenas e revisaveis.
- Preferir padroes nativos do Django.
- Documentar neste arquivo qualquer decisao arquitetural nova antes de implementa-la.
- Nao armazenar segredos no repositorio.
- Nao introduzir frameworks extras sem justificativa clara.

