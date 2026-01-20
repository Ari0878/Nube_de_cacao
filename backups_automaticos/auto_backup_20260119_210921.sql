-- Respaldo de Base de Datos - Nube de Cacao
-- Generado: 2026-01-19 21:09:21
-- Total de registros: 2

-- Crear tabla si no existe
CREATE TABLE IF NOT EXISTS ventas (
    id VARCHAR(255) PRIMARY KEY,
    cliente VARCHAR(255),
    tipo VARCHAR(100),
    cantidad INT,
    total DECIMAL(10, 2),
    fecha DATETIME
);

-- Datos
INSERT INTO ventas (id, cliente, tipo, cantidad, total, fecha) VALUES ('696ee82459b75c34d072eb8c', 'Juan', 'Capuchino', 3, 120.00, '2026-01-19 20:27:48');
INSERT INTO ventas (id, cliente, tipo, cantidad, total, fecha) VALUES ('696ee8f0115c2bca9a98e035', 'Fany', 'Latte', 23, 1035.00, '2026-01-19 20:31:12');