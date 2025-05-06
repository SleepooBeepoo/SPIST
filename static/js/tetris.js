// Tetris Game Implementation

document.addEventListener('DOMContentLoaded', () => {
    // Get the canvas element and its context
    const canvas = document.getElementById('tetris');
    const context = canvas.getContext('2d');
    
    // Scale blocks to 30px
    const scale = 30;
    
    // Set canvas dimensions
    canvas.width = 300;  // 10 blocks wide
    canvas.height = 600; // 20 blocks high
    
    // Draw grid lines
    context.scale(scale, scale);
    
    // Tetris pieces and their colors
    const pieces = [
        // I piece
        {
            shape: [
                [0, 0, 0, 0],
                [1, 1, 1, 1],
                [0, 0, 0, 0],
                [0, 0, 0, 0]
            ],
            color: '#00FFFF' // Cyan
        },
        // J piece
        {
            shape: [
                [1, 0, 0],
                [1, 1, 1],
                [0, 0, 0]
            ],
            color: '#0000FF' // Blue
        },
        // L piece
        {
            shape: [
                [0, 0, 1],
                [1, 1, 1],
                [0, 0, 0]
            ],
            color: '#FF7F00' // Orange
        },
        // O piece
        {
            shape: [
                [1, 1],
                [1, 1]
            ],
            color: '#FFFF00' // Yellow
        },
        // S piece
        {
            shape: [
                [0, 1, 1],
                [1, 1, 0],
                [0, 0, 0]
            ],
            color: '#00FF00' // Green
        },
        // T piece
        {
            shape: [
                [0, 1, 0],
                [1, 1, 1],
                [0, 0, 0]
            ],
            color: '#800080' // Purple
        },
        // Z piece
        {
            shape: [
                [1, 1, 0],
                [0, 1, 1],
                [0, 0, 0]
            ],
            color: '#FF0000' // Red
        }
    ];
    
    // Game variables
    let board = createBoard(10, 20);
    let currentPiece = null;
    let currentPosition = { x: 0, y: 0 };
    let score = 0;
    let gameOver = false;
    let gameInterval = null;
    let isPaused = false;
    
    // Create a new game board
    function createBoard(width, height) {
        return Array(height).fill().map(() => Array(width).fill(0));
    }
    
    // Generate a random piece
    function getRandomPiece() {
        const randomIndex = Math.floor(Math.random() * pieces.length);
        return JSON.parse(JSON.stringify(pieces[randomIndex])); // Deep copy
    }
    
    // Draw a single block
    function drawBlock(x, y, color) {
        context.fillStyle = color;
        context.fillRect(x, y, 1, 1);
        context.strokeStyle = '#000';
        context.strokeRect(x, y, 1, 1);
    }
    
    // Draw the board
    function drawBoard() {
        board.forEach((row, y) => {
            row.forEach((value, x) => {
                if (value) {
                    drawBlock(x, y, value);
                }
            });
        });
    }
    
    // Draw the current piece
    function drawPiece() {
        if (!currentPiece) return;
        
        currentPiece.shape.forEach((row, y) => {
            row.forEach((value, x) => {
                if (value) {
                    drawBlock(x + currentPosition.x, y + currentPosition.y, currentPiece.color);
                }
            });
        });
    }
    
    // Clear the canvas
    function clearCanvas() {
        context.clearRect(0, 0, canvas.width, canvas.height);
    }
    
    // Check if the current piece collides with the board or boundaries
    function checkCollision(piece, position) {
        for (let y = 0; y < piece.shape.length; y++) {
            for (let x = 0; x < piece.shape[y].length; x++) {
                if (piece.shape[y][x]) {
                    const boardX = x + position.x;
                    const boardY = y + position.y;
                    
                    // Check boundaries
                    if (boardX < 0 || boardX >= board[0].length || boardY >= board.length) {
                        return true;
                    }
                    
                    // Check collision with existing blocks
                    if (boardY >= 0 && board[boardY][boardX]) {
                        return true;
                    }
                }
            }
        }
        return false;
    }
    
    // Merge the current piece with the board
    function mergePiece() {
        currentPiece.shape.forEach((row, y) => {
            row.forEach((value, x) => {
                if (value) {
                    const boardY = y + currentPosition.y;
                    const boardX = x + currentPosition.x;
                    if (boardY >= 0) {
                        board[boardY][boardX] = currentPiece.color;
                    }
                }
            });
        });
    }
    
    // Rotate the current piece
    function rotatePiece() {
        const rotated = [];
        for (let i = 0; i < currentPiece.shape[0].length; i++) {
            const row = [];
            for (let j = currentPiece.shape.length - 1; j >= 0; j--) {
                row.push(currentPiece.shape[j][i]);
            }
            rotated.push(row);
        }
        
        const originalPiece = JSON.parse(JSON.stringify(currentPiece));
        currentPiece.shape = rotated;
        
        // If rotation causes collision, revert back
        if (checkCollision(currentPiece, currentPosition)) {
            currentPiece = originalPiece;
        }
    }
    
    // Move the current piece down
    function moveDown() {
        currentPosition.y++;
        if (checkCollision(currentPiece, currentPosition)) {
            currentPosition.y--;
            mergePiece();
            clearLines();
            spawnPiece();
            
            // Check if game over
            if (checkCollision(currentPiece, currentPosition)) {
                gameOver = true;
                clearInterval(gameInterval);
                alert('Game Over! Your score: ' + score);
                document.getElementById('start-button').textContent = 'Restart';
            }
        }
    }
    
    // Move the current piece left
    function moveLeft() {
        currentPosition.x--;
        if (checkCollision(currentPiece, currentPosition)) {
            currentPosition.x++;
        }
    }
    
    // Move the current piece right
    function moveRight() {
        currentPosition.x++;
        if (checkCollision(currentPiece, currentPosition)) {
            currentPosition.x--;
        }
    }
    
    // Clear completed lines
    function clearLines() {
        let linesCleared = 0;
        
        for (let y = board.length - 1; y >= 0; y--) {
            if (board[y].every(value => value)) {
                // Remove the line
                board.splice(y, 1);
                // Add a new empty line at the top
                board.unshift(Array(board[0].length).fill(0));
                linesCleared++;
                y++; // Check the same line again
            }
        }
        
        // Update score
        if (linesCleared > 0) {
            score += linesCleared * 100;
            document.getElementById('score').textContent = score;
        }
    }
    
    // Spawn a new piece
    function spawnPiece() {
        currentPiece = getRandomPiece();
        currentPosition = {
            x: Math.floor((board[0].length - currentPiece.shape[0].length) / 2),
            y: 0
        };
    }
    
    // Update the game state
    function update() {
        if (gameOver || isPaused) return;
        
        clearCanvas();
        drawBoard();
        drawPiece();
    }
    
    // Start the game
    function startGame() {
        if (gameInterval) {
            clearInterval(gameInterval);
        }
        
        board = createBoard(10, 20);
        score = 0;
        gameOver = false;
        isPaused = false;
        document.getElementById('score').textContent = score;
        document.getElementById('start-button').textContent = 'Restart';
        document.getElementById('pause-button').textContent = 'Pause';
        
        spawnPiece();
        gameInterval = setInterval(() => {
            moveDown();
            update();
        }, 500);
    }
    
    // Pause/resume the game
    function togglePause() {
        isPaused = !isPaused;
        document.getElementById('pause-button').textContent = isPaused ? 'Resume' : 'Pause';
    }
    
    // Event listeners for keyboard controls
    document.addEventListener('keydown', event => {
        if (gameOver || isPaused) return;
        
        switch (event.key) {
            case 'ArrowLeft':
                moveLeft();
                break;
            case 'ArrowRight':
                moveRight();
                break;
            case 'ArrowDown':
                moveDown();
                break;
            case 'ArrowUp':
                rotatePiece();
                break;
        }
        
        update();
    });
    
    // Event listeners for buttons
    document.getElementById('start-button').addEventListener('click', startGame);
    document.getElementById('pause-button').addEventListener('click', togglePause);
    
    // Initial draw
    update();
});