# Agents Guide - Django Blog

Este arquivo define a arquitetura inicial e as regras de trabalho para evoluir o projeto de blog em Django. A implementacao ainda nao deve ser executada automaticamente; primeiro vamos incrementar e validar este guia.

## Objetivo do projeto

Construir um blog em Django com:

1. Sistema de posts.
2. Banco de dados SQLite em desenvolvimento e PostgreSQL em producao.
3. Armazenamento de imagens em MinIO ja existente; o projeto nao deve criar instancia MinIO, apenas consumir buckets configurados por ambiente.
4. Sistema de comentarios usando Django.
5. Sempre manter um readme ok para o projeto em inglês.
6. O Visual do projeto deve-se utilizar o TailWind, sem compilação.

## Base de documentacao

Usar a documentacao do Django como referencia principal via Context7:

- Biblioteca Context7: `/django/django`
- Topicos consultados inicialmente:
  - Models e relacionamentos para aplicacoes de blog.
  - Configuracao `DATABASES` com backend PostgreSQL.
- `ImageField`, `FileField`, `MEDIA_URL`, `MEDIA_ROOT` e API de storage para MinIO ja existente.
  - Forms para entrada de comentarios.

Decisoes arquiteturais devem preferir APIs nativas do Django antes de criar abstracoes proprias.

## Arquitetura proposta

### Apps Django

Estrutura inicial sugerida:

- `blog`: posts, categorias/tags futuras, imagens de capa, listagem e detalhe de posts.
- `comments`: comentarios associados aos posts, moderacao e formulario publico.

O comments deve ser feito em um app serparado

### Views

Utilizar class based views, sempre que possível

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

### Bancos de dados

O ambiente de desenvolvimento deve usar SQLite por padrao. O ambiente de producao deve usar o backend oficial do Django para PostgreSQL:

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
- Usar SQLite no ambiente de desenvolvimento por simplicidade local, e PostgreSQL no ambiente de producao.
- Migrations devem ser pequenas e revisaveis.

### MinIO ja existente para imagens

MinIO deve ser tratado como storage S3-compativel ja provisionado fora deste projeto. O projeto Django nao deve criar, subir ou gerenciar a instancia MinIO.

Buckets por ambiente:

- Usar buckets separados por ambiente e uma boa pratica, por exemplo um bucket para desenvolvimento e outro para producao.
- O bucket de desenvolvimento deve ser usado apenas para testes locais e validacao de upload.
- O bucket de producao deve armazenar apenas arquivos reais de producao.
- A selecao do bucket deve vir de variaveis de ambiente, nunca de valores hardcoded.
- Buckets, endpoints, credenciais, politicas de acesso e dominios publicos devem ser tratados como configuracao externa ao Django.

Abordagem prevista:

- Usar `ImageField` nos models.
- Usar um backend de storage compativel com S3, como `django-storages` com `boto3`.
- Configurar endpoint, bucket, credenciais e URL publica do MinIO ja existente por variaveis de ambiente.

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
- Em desenvolvimento, o projeto deve apontar para o MinIO ja existente e para o bucket de desenvolvimento configurado.
- O Docker Compose deste repositorio nao deve subir MinIO por padrao.
- Nenhuma rotina do projeto deve criar buckets automaticamente sem pedido explicito.

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

- SQLite em desenvolvimento
- PostgreSQL em producao
- MinIO ja existente, com buckets separados por ambiente quando aplicavel
- Docker Compose para desenvolvimento local

## Ordem incremental sugerida

1. Validar este `agents.md`.
2. Criar o projeto Django base, se ainda nao existir.
3. Configurar variaveis de ambiente e settings por ambiente.
4. Adicionar PostgreSQL.
5. Criar app de posts.
6. Criar models, admin, urls, views e templates de posts.
7. Configurar storage de imagens apontando para o MinIO ja existente.
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

## Decisoes registradas na primeira implementacao

- O projeto Django base usa o pacote `config` para settings, URLs, ASGI e WSGI.
- A configuracao usa variaveis de ambiente via `os.environ`, sem dependencia extra de carregamento automatico de `.env`.
- O banco de desenvolvimento usa SQLite por padrao com `SQLITE_NAME_DEV`; producao usa PostgreSQL via variaveis `DB_*_PROD`.
- O storage S3/MinIO fica atras de `USE_S3_STORAGE=True`; em desenvolvimento sem essa flag, o storage local de media do Django continua disponivel.
- O MinIO e externo ao projeto; o repositorio nao deve criar instancia MinIO nem buckets por padrao.
- Ambientes diferentes podem usar buckets diferentes no mesmo MinIO, por exemplo um bucket para desenvolvimento e outro para producao.
- O `docker-compose.yml` inicial sobe apenas PostgreSQL, porque o MinIO e os buckets ja existem fora deste projeto.
- O editor WYSIWYG inicial do admin usa JavaScript local no campo `content`, evitando dependencia Python adicional e chaves externas de editor.
- Imagens coladas ou inseridas no editor WYSIWYG do admin devem ser enviadas para o storage padrao do Django em `posts/content/YYYY/MM/`, respeitando as mesmas validacoes de tipo e tamanho das imagens de capa.
- O Tailwind e carregado via CDN nos templates, sem pipeline de compilacao.
- Foram criadas migrations iniciais revisaveis, mas nenhuma migration foi executada automaticamente.
- `DJANGO_ENV` seleciona as configuracoes por ambiente: `development` usa variaveis com sufixo `_DEV`, e `production` usa variaveis com sufixo `_PROD`.
- PostgreSQL de producao e MinIO possuem variaveis separadas no `.env.example`; desenvolvimento usa SQLite e o bucket MinIO de desenvolvimento, sem registrar segredos reais no repositorio.
- O `docker-compose.yml` pode subir PostgreSQL para testes locais mais proximos de producao, mas nao e necessario para o banco padrao de desenvolvimento.
- Os buckets MinIO definidos para o projeto sao `djangoblogdev` e `djangoblogprod`; uploads de media devem usar `AWS_LOCATION=media` para gravar dentro da pasta `media` do bucket ativo.
- O container Django usa `docker-entrypoint.sh`; no startup, ele roda migrations se `RUN_MIGRATIONS_ON_STARTUP=true` e cria o superusuario inicial via `ensure_superuser` se `CREATE_SUPERUSER_ON_STARTUP=true`.
- O admin so deve mostrar o link "View on site" para posts que ja estejam publicos (`status=published` e `published_at` no passado), evitando 404 esperado ao tentar abrir rascunhos na area publica.
- A UI publica segue uma direcao blog-first inspirada em `https://guikastner.github.io/web/`: paleta premium em azul, topbar em capsula, fundo claro com grid sutil, cards arredondados, tipografia `Space Grotesk` + `Source Serif 4`, feed cronologico de posts e largura de leitura limitada em torno de `max-w-[46rem]` no detalhe. O foco deve continuar visivel, alvos interativos devem ter pelo menos 44px de altura e formularios devem manter labels/erros acessiveis. O Tailwind continua carregado via CDN, sem pipeline de compilacao.
- A barra de navegacao publica usa icones SVG inline com `currentColor`, mantendo os icones visiveis sem adicionar biblioteca de icones ou etapa de build. As acoes editoriais sao condicionadas por permissoes nativas do Django: `blog.add_post` mostra o atalho de novo post, `blog.change_post` mostra edicao no detalhe do post, e `user.is_staff` mostra o admin.
