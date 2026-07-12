import React from 'react';

function Button({ children, variant = 'primary', onClick, ...props }) {
  return (
    <button className={`btn ${variant === 'secondary' ? 'btn-secondary' : ''}`} onClick={onClick} {...props}>
      {children}
    </button>
  );
}

export default Button;
