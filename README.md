# Email Composer CC and BCC

Módulo personalizado para Odoo 19.

## Funcionalidades

- Adiciona os campos **CC** e **BCC** aos compositores de email do Odoo.
- Disponível no chatter, envio de cotações, encomendas e faturas individuais.
- Permite pesquisar e selecionar contactos ou introduzir endereços de email manualmente.
- Envia cópias dos emails aos destinatários CC e BCC.
- Preserva a formatação HTML e os anexos originais, incluindo PDFs de faturas.
- Impede o envio duplicado quando um endereço está simultaneamente em Para e CC/BCC.
- Regista os destinatários Para, CC e BCC no histórico interno do chatter.
- Mantém os destinatários BCC ocultos dos restantes destinatários.

## Comportamento dos emails

- **Para:** recebe o email com o comportamento normal do Odoo.
- **CC:** recebe uma cópia do email, sem botões ou rodapés específicos de cotações.
- **BCC:** recebe uma cópia oculta, sem botões ou rodapés específicos de cotações.
- Os anexos e o conteúdo original da mensagem são preservados.
- Os campos CC/BCC não são apresentados em envios de email marketing em massa.

## Versão 19.0.1.9.0

- Adiciona CC/BCC ao envio de faturas individuais através de **Enviar** e **Enviar e Imprimir**.
- Permite pesquisar contactos nos campos CC/BCC.
- Garante a transmissão dos destinatários CC/BCC para o envio efetivo do email.
- Mantém os anexos e a formatação original.
- Preserva a separação entre os destinatários principais e os destinatários CC/BCC.

## Limitações

- Não abrange o envio de várias faturas em simultâneo.
- Não altera automaticamente todos os emails gerados pelo sistema.
- Compositores personalizados de outros módulos podem necessitar de integração adicional.

## Atualização

1. Efetuar backup da base de dados.
2. Substituir a pasta `mail_composer_cc_bcc`.
3. Reiniciar o Odoo.
4. Atualizar o módulo.
5. Atualizar o navegador (`Ctrl + F5`).
6. Testar o envio de emails com CC/BCC no chatter, nas cotações e nas faturas.

**Dependências:** `mail` e `account`.

**Nota:** Recomenda-se testar em pré-produção com SMTP funcional, verificando a receção dos emails, os anexos e a privacidade dos destinatários BCC.
