CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    value BIGINT NOT NULL,                 
    operation INTEGER NOT NULL,       
    type INTEGER NOT NULL,         
    datetime TIMESTAMP NOT NULL,
    category_id INTEGER NOT NULL,
    user_id UUID NOT NULL,
    CONSTRAINT fk_transaction_category FOREIGN KEY (category_id) REFERENCES categories(id),
    CONSTRAINT fk_transaction_user FOREIGN KEY (user_id) REFERENCES users(id)
);