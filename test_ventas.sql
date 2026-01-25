-- ========================================
-- Respaldo de Ventas - Nube de Cacao
-- Generado el: 2026-01-19 20:33:18
-- ========================================

-- Crear tabla si no existe
CREATE TABLE IF NOT EXISTS ventas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente VARCHAR(255),
    tipo VARCHAR(100),
    cantidad INT,
    total DECIMAL(10,2),
    fecha DATETIME
);

-- Limpiar tabla antes de insertar
TRUNCATE TABLE ventas;

-- Insertar datos
INSERT INTO ventas (cliente, tipo, cantidad, total, fecha) VALUES ('Juan Pérez', 'Espresso', 2, 60.0, '2026-01-19 20:33:18');
INSERT INTO ventas (cliente, tipo, cantidad, total, fecha) VALUES ('María González', 'Cappuccino', 3, 135.0, '2026-01-19 20:33:18');
INSERT INTO ventas (cliente, tipo, cantidad, total, fecha) VALUES ('Carlos López', 'Latte', 1, 55.0, '2026-01-19 20:33:18');

-- Fin del respaldo