CREATE TABLE balances (
    id SERIAL PRIMARY KEY,
    balance BIGINT NOT NULL,
    datetime TIMESTAMP NOT NULL DEFAULT NOW(),
    user_id UUID NOT NULL,
    CONSTRAINT fk_transaction_user FOREIGN KEY (user_id) REFERENCES users(id)
)